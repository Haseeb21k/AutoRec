import os
import json
import time
import tempfile
import google.generativeai as genai
from typing import List, Dict, Optional
from decimal import Decimal
from datetime import datetime
from app.schemas.normalization import UnifiedTransaction
from .base_strategy import BaseStrategy
from dotenv import load_dotenv

load_dotenv()

class PDFStrategy(BaseStrategy):
    def __init__(self):
        # Initialize Gemini API
        self.api_key = os.getenv("API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set.")
        
        genai.configure(api_key=self.api_key)
        # We use Flash 001 specific version
        self.model = genai.GenerativeModel(model_name="models/gemini-2.5-flash")

    def parse(self, content: bytes, **kwargs) -> List[UnifiedTransaction]:
        """
        Extracts transactions from PDF bytes using AI (Gemini 1.5 Flash).
        """
        transactions = []
        temp_pdf_path = None
        remote_file = None

        try:
            # 1. PREPARE FILE
            # The Gemini API requires a file path (not raw bytes), so we create a temp file.
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_pdf:
                temp_pdf.write(content)
                temp_pdf_path = temp_pdf.name

            # 2. UPLOAD TO AI
            # Upload the file to Google's GenAI storage
            remote_file = genai.upload_file(path=temp_pdf_path, display_name="Bank_Statement_Upload")

            # Wait for file processing (State must be 'ACTIVE' before inference)
            while remote_file.state.name == "PROCESSING":
                time.sleep(1)
                remote_file = genai.get_file(remote_file.name)

            if remote_file.state.name == "FAILED":
                raise ValueError("AI failed to process the PDF file structure.")

            # 3. CONSTRUCT PROMPT
            # We enforce a strict JSON schema in the prompt
            prompt = """
            Act as a financial data parser. Analyze the uploaded bank statement PDF.
            Extract all transaction rows found in the statement tables.
            
            Return the data STRICTLY as a JSON list of objects. 
            Do not include markdown formatting (like ```json).
            
            Use this specific schema for every item:
            {
                "date": "YYYY-MM-DD",
                "description": "Full description string",
                "amount": float (negative for debits/withdrawals, positive for credits/deposits),
                "reference": "Transaction ID/Ref/Check# if present, else null"
            }
            """

            # 4. RUN INFERENCE
            response = self.model.generate_content(
                [remote_file, prompt],
                generation_config={"response_mime_type": "application/json"}
            )

            # 5. PARSE & NORMALIZE
            try:
                extracted_data = json.loads(response.text)
            except json.JSONDecodeError:
                # Log error in production
                print(f"AI Response was not valid JSON: {response.text}")
                return []

            for idx, item in enumerate(extracted_data):
                # Basic validation
                if not item.get("date") or item.get("amount") is None:
                    continue

                try:
                    # Convert AI string date "YYYY-MM-DD" to Python date object
                    tx_date = datetime.strptime(item["date"], "%Y-%m-%d").date()
                    
                    # Convert float to Decimal for financial precision
                    tx_amount = Decimal(str(item["amount"]))
                    
                    # Create UnifiedTransaction
                    tx = UnifiedTransaction(
                        date=tx_date,
                        amount=tx_amount,
                        description=item.get("description", "").strip(),
                        # Generate a unique ref combining AI file ID and index
                        external_ref_id=f"AI-{remote_file.name.split('/')[-1]}-{idx}",
                        source_format="pdf-ai",
                        confidence_score=0.95, # AI extraction is generally high confidence
                        raw_source=json.dumps(item)
                    )
                    transactions.append(tx)
                except Exception as e:
                    print(f"Skipping row due to parsing error: {e}")
                    continue

        finally:
            # 6. CLEANUP
            # Remove local temp file
            if temp_pdf_path and os.path.exists(temp_pdf_path):
                os.unlink(temp_pdf_path)
            
            # Remove remote file from Gemini Cloud to ensure privacy/cleanup
            if remote_file:
                try:
                    genai.delete_file(remote_file.name)
                except Exception:
                    pass

        return transactions