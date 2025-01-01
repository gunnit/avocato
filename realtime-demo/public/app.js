// Core session management
let pc = null;
let dc = null;
let audioEl = null;

async function startSession() {
    try {
        // Get ephemeral token from server
        const tokenResponse = await fetch("/session");
        const data = await tokenResponse.json();
        const EPHEMERAL_KEY = data.client_secret.value;

        // Create WebRTC peer connection
        pc = new RTCPeerConnection();
        
        // Setup audio element for model output
        audioEl = document.createElement("audio");
        audioEl.autoplay = true;
        pc.ontrack = e => audioEl.srcObject = e.streams[0];

        // Get microphone access and add track
        const ms = await navigator.mediaDevices.getUserMedia({ audio: true });
        pc.addTrack(ms.getTracks()[0]);

        // Create data channel for events
        dc = pc.createDataChannel("oai-events");
        setupDataChannel();

        // Create and set local description
        const offer = await pc.createOffer();
        await pc.setLocalDescription(offer);

        // Connect to OpenAI Realtime API
        const baseUrl = "https://api.openai.com/v1/realtime";
        const model = "gpt-4o-realtime-preview-2024-12-17";
        const sdpResponse = await fetch(`${baseUrl}?model=${model}`, {
            method: "POST", 
            body: offer.sdp,
            headers: {
                Authorization: `Bearer ${EPHEMERAL_KEY}`,
                "Content-Type": "application/sdp"
            }
        });

        const answer = {
            type: "answer",
            sdp: await sdpResponse.text()
        };
        await pc.setRemoteDescription(answer);

        // Update UI
        document.getElementById("status").className = "status connected";
        document.getElementById("status").textContent = "Connesso";
        document.getElementById("startBtn").disabled = true;
        document.getElementById("stopBtn").disabled = false;
        document.getElementById("sendBtn").disabled = false;

    } catch (error) {
        console.error("Errore di avvio sessione:", error);
        document.getElementById("status").textContent = `Errore: ${error.message}`;
    }
}

function setupDataChannel() {
    dc.onopen = () => {
        console.log("Canale dati aperto");
        // Set initial session config
        dc.send(JSON.stringify({
            type: "session.update",
            session: {
                instructions: `Sei un assistente legale AI esperto specializzato nel diritto penale italiano e nel Codice Penale italiano.
                Le tue risposte devono:
                - Essere precise e fare riferimento a specifici articoli del Codice Penale quando applicabile
                - Spiegare i concetti legali in un linguaggio chiaro e professionale
                - Fornire contesto su come le leggi sono tipicamente interpretate dai tribunali italiani
                - Includere esempi pertinenti di giurisprudenza quando utili
                - Chiarire eventuali differenze tra teoria e applicazione pratica
                - Mantenere sempre un tono formale e professionale
                - Quando si discute di pene, specificare sempre se si tratta di pene massime e quali fattori potrebbero influenzare la sentenza
                
                Importante: Includere sempre un disclaimer che queste sono informazioni generali e non costituiscono consulenza legale, e che gli utenti dovrebbero consultare un avvocato qualificato per casi specifici.`,
            }
        }));
    };

    dc.onmessage = (e) => {
        const event = JSON.parse(e.data);
        handleServerEvent(event);
    };
}

function handleServerEvent(event) {
    const conversation = document.getElementById("conversation");
    
    switch(event.type) {
        case "response.text.delta":
            // Handle streaming text response
            let responseDiv = conversation.querySelector(".current-response");
            if (!responseDiv) {
                responseDiv = document.createElement("div");
                responseDiv.className = "assistant current-response";
                conversation.appendChild(responseDiv);
            }
            responseDiv.textContent += event.delta;
            break;

        case "response.done":
            // Remove current-response class when done
            const currentResponse = conversation.querySelector(".current-response");
            if (currentResponse) {
                currentResponse.classList.remove("current-response");
            }
            break;
    }

    // Auto-scroll conversation
    conversation.scrollTop = conversation.scrollHeight;
}

function useQuery(text) {
    document.getElementById('textInput').value = text;
    sendMessage();
}

function sendMessage() {
    const textInput = document.getElementById("textInput");
    const text = textInput.value.trim();
    if (!text) return;

    // Add user message to conversation
    const conversation = document.getElementById("conversation");
    const userDiv = document.createElement("div");
    userDiv.className = "user";
    userDiv.textContent = text;
    conversation.appendChild(userDiv);

    // Send message to model
    dc.send(JSON.stringify({
        type: "conversation.item.create",
        item: {
            type: "message",
            role: "user",
            content: [{
                type: "input_text",
                text: text
            }]
        }
    }));

    // Request response
    dc.send(JSON.stringify({
        type: "response.create",
        response: {
            modalities: ["text"]
        }
    }));

    // Clear input
    textInput.value = "";
}

function stopSession() {
    if (pc) {
        pc.close();
        pc = null;
    }
    if (audioEl) {
        audioEl.srcObject = null;
        audioEl = null;
    }
    document.getElementById("status").className = "status disconnected";
    document.getElementById("status").textContent = "Disconnesso";
    document.getElementById("startBtn").disabled = false;
    document.getElementById("stopBtn").disabled = true;
    document.getElementById("sendBtn").disabled = true;
}

// Event listeners
document.addEventListener('DOMContentLoaded', () => {
    document.getElementById("startBtn").onclick = startSession;
    document.getElementById("stopBtn").onclick = stopSession;
    document.getElementById("sendBtn").onclick = sendMessage;
    document.getElementById("textInput").onkeypress = (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    };
});
