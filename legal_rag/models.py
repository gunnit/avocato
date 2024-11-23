from django.db import models

class PenalCodeBook(models.Model):
    number = models.IntegerField()
    name = models.CharField(max_length=255)
    description = models.TextField()
    
    class Meta:
        ordering = ['number']
    
    def __str__(self):
        return f"Libro {self.number} - {self.name}"

class PenalCodeTitle(models.Model):
    book = models.ForeignKey(PenalCodeBook, on_delete=models.CASCADE, related_name='titles')
    number = models.IntegerField()
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    articles_range = models.CharField(max_length=50)  # e.g., "artt. 1-16"
    
    class Meta:
        ordering = ['book', 'number']
    
    def __str__(self):
        return f"Titolo {self.number} - {self.name}"

class PenalCodeSection(models.Model):
    title = models.ForeignKey(PenalCodeTitle, on_delete=models.CASCADE, related_name='sections')
    number = models.IntegerField()
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    
    class Meta:
        ordering = ['title', 'number']
    
    def __str__(self):
        return f"Sezione {self.number} - {self.name}"

class PenalCodeArticle(models.Model):
    title = models.ForeignKey(PenalCodeTitle, on_delete=models.CASCADE, related_name='articles')
    section = models.ForeignKey(PenalCodeSection, on_delete=models.SET_NULL, null=True, blank=True, related_name='articles')
    number = models.IntegerField()
    heading = models.CharField(max_length=255)  # The article name/title
    description = models.TextField(blank=True)  # The article description
    content = models.TextField()  # The actual article text
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['number']
    
    def __str__(self):
        return f"Art. {self.number} - {self.heading}"
