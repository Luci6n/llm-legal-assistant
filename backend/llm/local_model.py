from prompt_templates import METADATA_EXTRACTION_PROMPT, SENSITIVE_INFORMATION_REDACT_PROMPT
from ollama import Client

def create_metadata_extractor():
    # Initialize Ollama client
    client = Client()
    # Determine if prompt is available
    if METADATA_EXTRACTION_PROMPT is not None:
        # Metadata extraction
        response = client.create(
            model = 'metadata-extractor',
            from_ = 'gemma3n:e2b-it-q4_K_M',
            system = METADATA_EXTRACTION_PROMPT,
            stream = False,
        )
        
        if(response.status_code == 200):
            print("Metadata Extraction model initialized successfully.")
        
        return client
            
def create_sensitive_info_redactor():
    # Initialize Ollama client
    client = Client()
    # Determine if prompt is available
    if SENSITIVE_INFORMATION_REDACT_PROMPT is not None:
        # Sensitive information redaction
        response = client.create(
            model = 'sensitive-info-redactor',
            from_ = 'gemma3n:e2b-it-q4_K_M',
            system = SENSITIVE_INFORMATION_REDACT_PROMPT,
            stream = False,
        )
        
        if(response.status_code == 200):
            print("Sensitive Information Redaction model initialized successfully.")
        
        return client
