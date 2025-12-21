from typing import List, Dict
from fastapi import UploadFile, HTTPException
from app.schemas.normalization import UnifiedTransaction
from parsers.csv_strategy import CSVStrategy
from parsers.mt940_strategy import MT940Strategy
from parsers.pdf_strategy import PDFStrategy

class NormalizationService:
    """
    Orchestrator for file normalization.
    Selects the correct strategy based on file type and returns UnifiedTransactions.
    """
    
    @staticmethod
    async def normalize_file(file: UploadFile, column_mapping: Dict[str, str] = None) -> List[UnifiedTransaction]:
        content = await file.read()
        filename = file.filename.lower()
        
        # Reset cursor since we read it
        await file.seek(0)
        
        try:
            if filename.endswith('.csv') or filename.endswith('.xlsx'):
                if not column_mapping:
                    # Default mapping if none provided
                    column_mapping = {'date': 'Date', 'amount': 'Amount', 'description': 'Description'}
                strategy = CSVStrategy()
                return strategy.parse(content, column_mapping=column_mapping)
                
            elif filename.endswith('.sta') or filename.endswith('.txt'):
                # MT940 is text-based
                content_str = content.decode("utf-8")
                strategy = MT940Strategy()
                return strategy.parse(content_str)
                
            elif filename.endswith('.pdf'):
                strategy = PDFStrategy()
                return strategy.parse(content)
                
            else:
                raise HTTPException(status_code=400, detail=f"Unsupported file format: {filename}")
                
        except Exception as e:
            # Log the full error for debugging
            import traceback
            traceback.print_exc()
            print(f"FAILED TO NORMALIZE: {str(e)}")
            
            # Re-raise HTTP exceptions, wrap others
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(status_code=400, detail=f"Normalization failed: {str(e)}")
