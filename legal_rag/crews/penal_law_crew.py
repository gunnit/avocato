from crewai import Agent, Task, Crew, Process
from crewai.project import CrewBase, agent, task, crew
from langchain.tools import Tool
from typing import Dict, Any
import json

@CrewBase
class PenalLawCrew:
    """A specialized crew for analyzing cases in the context of Italian penal law"""

    @agent
    def legal_researcher(self) -> Agent:
        return Agent(
            role="Legal Research Specialist",
            goal="Analyze case details and identify relevant articles from the Italian Penal Code",
            backstory="""You are an expert in Italian criminal law with years of experience 
            in legal research. Your expertise lies in analyzing case details and identifying 
            relevant legal precedents and articles from the Italian Penal Code.""",
            verbose=True,
            allow_delegation=False
        )

    @agent
    def case_analyzer(self) -> Agent:
        return Agent(
            role="Case Analysis Expert",
            goal="Provide comprehensive analysis of case elements in relation to penal law",
            backstory="""You are a seasoned legal analyst specializing in criminal cases. 
            You excel at breaking down complex cases and identifying key elements that align 
            with specific articles of the penal code.""",
            verbose=True,
            allow_delegation=False
        )

    @agent
    def legal_strategist(self) -> Agent:
        return Agent(
            role="Legal Strategy Expert",
            goal="Develop legal strategies based on case analysis and penal code interpretation",
            backstory="""You are a strategic legal advisor with deep knowledge of Italian 
            criminal proceedings. You specialize in developing comprehensive legal strategies 
            by combining case analysis with penal code interpretations.""",
            verbose=True,
            allow_delegation=False
        )

    @task
    def analyze_case_details(self) -> Task:
        return Task(
            description="""Analyze the provided case details and identify key elements relevant 
            to Italian criminal law. Extract important facts, circumstances, and potential 
            legal issues.""",
            expected_output="""A structured analysis of the case highlighting key elements, 
            potential legal issues, and relevant circumstances.""",
            agent=self.legal_researcher()
        )

    @task
    def identify_relevant_articles(self) -> Task:
        return Task(
            description="""Based on the case analysis, identify and explain relevant articles 
            from the Italian Penal Code. Focus on articles that directly relate to the 
            identified legal issues.""",
            expected_output="""A list of relevant penal code articles with explanations of 
            their applicability to the case.""",
            agent=self.case_analyzer()
        )

    @task
    def develop_legal_strategy(self) -> Task:
        return Task(
            description="""Develop a comprehensive legal strategy based on the case analysis 
            and identified penal code articles. Include potential arguments, defenses, and 
            procedural considerations.""",
            expected_output="""A detailed legal strategy document outlining recommended 
            approaches, potential arguments, and key considerations.""",
            agent=self.legal_strategist()
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=[
                self.legal_researcher(),
                self.case_analyzer(),
                self.legal_strategist()
            ],
            tasks=[
                self.analyze_case_details(),
                self.identify_relevant_articles(),
                self.develop_legal_strategy()
            ],
            process=Process.sequential,
            verbose=True
        )

    def kickoff(self, case_details: Dict[str, Any]) -> Dict[str, Any]:
        """
        Start the crew's analysis process with the provided case details
        
        Args:
            case_details: Dictionary containing relevant case information
            
        Returns:
            Dictionary containing the analysis results and recommendations
        """
        result = self.crew().kickoff(inputs={"case_details": json.dumps(case_details)})
        return result
