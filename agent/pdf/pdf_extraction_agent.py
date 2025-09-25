import PyPDF2
import pdfplumber
import pandas as pd
import re
from pathlib import Path
from typing import Dict, List, Any, Optional
import json

class PDFExtractionAgent:
    def __init__(self):
        self.extracted_data = {}
        
    def extract_text_pypdf2(self, pdf_path: str) -> str:
        """Extract text using PyPDF2"""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                return text
        except Exception as e:
            print(f"Error with PyPDF2: {e}")
            return ""
            
    def extract_text_pdfplumber(self, pdf_path: str) -> Dict[str, Any]:
        """Extract text and tables using pdfplumber"""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                text = ""
                tables = []
                
                for i, page in enumerate(pdf.pages):
                    # Extract text
                    page_text = page.extract_text()
                    if page_text:
                        text += f"\n--- Page {i+1} ---\n{page_text}\n"
                    
                    # Extract tables
                    page_tables = page.extract_tables()
                    for j, table in enumerate(page_tables):
                        tables.append({
                            'page': i+1,
                            'table_index': j,
                            'data': table
                        })
                        
                return {
                    'text': text,
                    'tables': tables,
                    'num_pages': len(pdf.pages)
                }
        except Exception as e:
            print(f"Error with pdfplumber: {e}")
            return {'text': '', 'tables': [], 'num_pages': 0}
            
    def extract_healthcare_plan_info(self, text: str) -> Dict[str, Any]:
        """Extract healthcare plan specific information"""
        plan_info = {}
        
        # Extract plan name
        plan_name_pattern = r'(?:Plan Name|Plan|Coverage):\s*([^\n]+)'
        plan_match = re.search(plan_name_pattern, text, re.IGNORECASE)
        if plan_match:
            plan_info['plan_name'] = plan_match.group(1).strip()
            
        # Extract premium information
        premium_patterns = [
            r'Premium:\s*\$?(\d+(?:\.\d{2})?)',
            r'Monthly Premium:\s*\$?(\d+(?:\.\d{2})?)',
            r'\$(\d+(?:\.\d{2})?)\s*per month'
        ]
        for pattern in premium_patterns:
            premium_match = re.search(pattern, text, re.IGNORECASE)
            if premium_match:
                plan_info['monthly_premium'] = float(premium_match.group(1))
                break
                
        # Extract deductible
        deductible_patterns = [
            r'Deductible:\s*\$?(\d+(?:,\d{3})*(?:\.\d{2})?)',
            r'Annual Deductible:\s*\$?(\d+(?:,\d{3})*(?:\.\d{2})?)'
        ]
        for pattern in deductible_patterns:
            ded_match = re.search(pattern, text, re.IGNORECASE)
            if ded_match:
                plan_info['deductible'] = float(ded_match.group(1).replace(',', ''))
                break
                
        # Extract out-of-pocket maximum
        oop_patterns = [
            r'Out-of-pocket maximum:\s*\$?(\d+(?:,\d{3})*(?:\.\d{2})?)',
            r'Maximum out-of-pocket:\s*\$?(\d+(?:,\d{3})*(?:\.\d{2})?)',
            r'OOP Max:\s*\$?(\d+(?:,\d{3})*(?:\.\d{2})?)'
        ]
        for pattern in oop_patterns:
            oop_match = re.search(pattern, text, re.IGNORECASE)
            if oop_match:
                plan_info['oop_maximum'] = float(oop_match.group(1).replace(',', ''))
                break
                
        # Extract copay information
        copay_pattern = r'Copay:\s*\$?(\d+(?:\.\d{2})?)'
        copay_matches = re.findall(copay_pattern, text, re.IGNORECASE)
        if copay_matches:
            plan_info['copays'] = [float(match) for match in copay_matches]
            
        # Extract coinsurance
        coinsurance_pattern = r'Coinsurance:\s*(\d+)%'
        coinsurance_match = re.search(coinsurance_pattern, text, re.IGNORECASE)
        if coinsurance_match:
            plan_info['coinsurance'] = int(coinsurance_match.group(1))
            
        return plan_info
        
    def extract_coverage_benefits(self, text: str, tables: List[Dict]) -> List[Dict[str, Any]]:
        """Extract coverage benefits from text and tables"""
        benefits = []
        
        # Look for benefit information in tables
        for table_info in tables:
            table = table_info['data']
            if not table or len(table) < 2:
                continue
                
            headers = [str(cell).strip().lower() if cell else '' for cell in table[0]]
            
            # Check if this looks like a benefits table
            benefit_keywords = ['service', 'benefit', 'coverage', 'copay', 'coinsurance', 'cost']
            if any(keyword in ' '.join(headers) for keyword in benefit_keywords):
                for row in table[1:]:
                    if row and len(row) >= 2:
                        benefit = {
                            'service': str(row[0]).strip() if row[0] else '',
                            'details': [str(cell).strip() if cell else '' for cell in row[1:]]
                        }
                        if benefit['service']:
                            benefits.append(benefit)
                            
        return benefits
        
    def process_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """Complete PDF processing pipeline"""
        print(f"Processing PDF: {pdf_path}")
        
        # Extract content using pdfplumber (more reliable for tables)
        extracted = self.extract_text_pdfplumber(pdf_path)
        
        if not extracted['text']:
            # Fallback to PyPDF2 if pdfplumber fails
            print("Falling back to PyPDF2...")
            extracted['text'] = self.extract_text_pypdf2(pdf_path)
            
        # Extract healthcare-specific information
        plan_info = self.extract_healthcare_plan_info(extracted['text'])
        benefits = self.extract_coverage_benefits(extracted['text'], extracted.get('tables', []))
        
        result = {
            'file_path': pdf_path,
            'num_pages': extracted.get('num_pages', 0),
            'raw_text': extracted['text'],
            'tables': extracted.get('tables', []),
            'plan_info': plan_info,
            'benefits': benefits,
            'extraction_timestamp': pd.Timestamp.now().isoformat()
        }
        
        self.extracted_data[pdf_path] = result
        return result
        
    def save_extracted_data(self, output_path: str = "extracted_pdf_data.json"):
        """Save all extracted data to JSON file"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.extracted_data, f, indent=2, ensure_ascii=False)
        print(f"Extracted data saved to: {output_path}")
        
    def export_to_csv(self, pdf_path: str, output_dir: str = "extracted_data"):
        """Export extracted data to CSV files"""
        if pdf_path not in self.extracted_data:
            print(f"No data found for {pdf_path}")
            return
            
        Path(output_dir).mkdir(exist_ok=True)
        data = self.extracted_data[pdf_path]
        
        # Export plan info
        if data['plan_info']:
            plan_df = pd.DataFrame([data['plan_info']])
            plan_csv_path = Path(output_dir) / f"{Path(pdf_path).stem}_plan_info.csv"
            plan_df.to_csv(plan_csv_path, index=False)
            print(f"Plan info exported to: {plan_csv_path}")
            
        # Export benefits
        if data['benefits']:
            benefits_df = pd.DataFrame(data['benefits'])
            benefits_csv_path = Path(output_dir) / f"{Path(pdf_path).stem}_benefits.csv"
            benefits_df.to_csv(benefits_csv_path, index=False)
            print(f"Benefits exported to: {benefits_csv_path}")
            
        # Export tables
        for i, table_info in enumerate(data['tables']):
            if table_info['data']:
                table_df = pd.DataFrame(table_info['data'])
                table_csv_path = Path(output_dir) / f"{Path(pdf_path).stem}_table_{i+1}.csv"
                table_df.to_csv(table_csv_path, index=False)
                print(f"Table {i+1} exported to: {table_csv_path}")

if __name__ == "__main__":
    agent = PDFExtractionAgent()
    
    # Test with the specified PDF
    pdf_path = "data/plans_pdf/blue_advantage_gold_hmo_standard.pdf"
    
    if Path(pdf_path).exists():
        result = agent.process_pdf(pdf_path)
        
        print("\n=== EXTRACTION RESULTS ===")
        print(f"Pages: {result['num_pages']}")
        print(f"Tables found: {len(result['tables'])}")
        print(f"Plan info extracted: {bool(result['plan_info'])}")
        print(f"Benefits found: {len(result['benefits'])}")
        
        if result['plan_info']:
            print("\nPlan Information:")
            for key, value in result['plan_info'].items():
                print(f"  {key}: {value}")
                
        # Save results
        agent.save_extracted_data()
        agent.export_to_csv(pdf_path)
        
        print("\n=== RAW TEXT PREVIEW ===")
        print(result['raw_text'][:500] + "..." if len(result['raw_text']) > 500 else result['raw_text'])
        
    else:
        print(f"PDF file not found: {pdf_path}")
        print("Available PDF files:")
        pdf_dir = Path("data/plans_pdf")
        if pdf_dir.exists():
            for pdf_file in pdf_dir.glob("*.pdf"):
                print(f"  - {pdf_file}")