#!/usr/bin/env python3
"""
Mortgage Amortization Calculator

This script calculates mortgage payments and generates a complete amortization schedule.
It shows monthly payment breakdowns including principal, interest, and remaining balance.
"""

import argparse
import sys
from typing import List, Dict, Tuple
from datetime import datetime, date
from dateutil.relativedelta import relativedelta


class MortgageCalculator:
    def __init__(self, principal: float, annual_rate: float, years: int, start_date: date = None):
        """
        Initialize mortgage calculator.
        
        Args:
            principal: Loan amount ($)
            annual_rate: Annual interest rate (as percentage, e.g., 3.5 for 3.5%)
            years: Loan term in years
            start_date: Start date of the loan (defaults to today)
        """
        self.principal = principal
        self.annual_rate = annual_rate / 100  # Convert percentage to decimal
        self.years = years
        self.months = years * 12
        self.monthly_rate = self.annual_rate / 12
        self.start_date = start_date or date.today()
        
        # Calculate monthly payment using the standard mortgage formula
        if self.monthly_rate == 0:
            self.monthly_payment = principal / self.months
        else:
            self.monthly_payment = principal * (
                self.monthly_rate * (1 + self.monthly_rate) ** self.months
            ) / ((1 + self.monthly_rate) ** self.months - 1)
    
    def calculate_payment_breakdown(self, remaining_balance: float) -> Tuple[float, float]:
        """
        Calculate interest and principal portions of a payment.
        
        Args:
            remaining_balance: Current loan balance
            
        Returns:
            Tuple of (interest_payment, principal_payment)
        """
        interest_payment = remaining_balance * self.monthly_rate
        principal_payment = self.monthly_payment - interest_payment
        return interest_payment, principal_payment
    
    def generate_amortization_schedule(self) -> List[Dict]:
        """
        Generate complete amortization schedule.
        
        Returns:
            List of dictionaries containing payment details for each month
        """
        schedule = []
        remaining_balance = self.principal
        current_date = self.start_date
        
        for payment_num in range(1, self.months + 1):
            # Calculate payment breakdown
            interest_payment, principal_payment = self.calculate_payment_breakdown(remaining_balance)
            
            # Adjust for final payment (handle rounding)
            if payment_num == self.months:
                principal_payment = remaining_balance
                total_payment = interest_payment + principal_payment
            else:
                total_payment = self.monthly_payment
            
            # Update balance
            remaining_balance -= principal_payment
            
            # Create payment record
            payment_record = {
                'payment_number': payment_num,
                'date': current_date.strftime('%Y-%m-%d'),
                'payment_amount': total_payment,
                'principal': principal_payment,
                'interest': interest_payment,
                'remaining_balance': max(0, remaining_balance)  # Ensure non-negative
            }
            
            schedule.append(payment_record)
            
            # Move to next month
            current_date += relativedelta(months=1)
        
        return schedule
    
    def get_loan_summary(self) -> Dict:
        """Get summary of loan terms and totals."""
        schedule = self.generate_amortization_schedule()
        
        total_payments = sum(payment['payment_amount'] for payment in schedule)
        total_interest = sum(payment['interest'] for payment in schedule)
        
        return {
            'loan_amount': self.principal,
            'annual_interest_rate': self.annual_rate * 100,
            'loan_term_years': self.years,
            'monthly_payment': self.monthly_payment,
            'total_payments': total_payments,
            'total_interest': total_interest,
            'total_cost': total_payments,
            'start_date': self.start_date.strftime('%Y-%m-%d')
        }
    
    def print_summary(self):
        """Print loan summary to console."""
        summary = self.get_loan_summary()
        
        print("=" * 60)
        print("MORTGAGE LOAN SUMMARY")
        print("=" * 60)
        print(f"Loan Amount:           ${summary['loan_amount']:,.2f}")
        print(f"Interest Rate:         {summary['annual_interest_rate']:.3f}%")
        print(f"Loan Term:             {summary['loan_term_years']} years")
        print(f"Start Date:            {summary['start_date']}")
        print(f"Monthly Payment:       ${summary['monthly_payment']:,.2f}")
        print(f"Total of Payments:     ${summary['total_payments']:,.2f}")
        print(f"Total Interest Paid:   ${summary['total_interest']:,.2f}")
        print("=" * 60)
    
    def print_amortization_table(self, show_all: bool = False):
        """
        Print amortization schedule as a formatted table.
        
        Args:
            show_all: If False, shows only first 12 months and last 12 months
        """
        schedule = self.generate_amortization_schedule()
        
        print("\nAMORTIZATION SCHEDULE")
        print("=" * 100)
        print(f"{'Payment':<8} {'Date':<12} {'Payment':<12} {'Principal':<12} {'Interest':<12} {'Balance':<12}")
        print(f"{'Number':<8} {'':<12} {'Amount':<12} {'':<12} {'':<12} {'Remaining':<12}")
        print("-" * 100)
        
        if show_all or len(schedule) <= 24:
            # Show all payments if requested or if short term
            for payment in schedule:
                self._print_payment_row(payment)
        else:
            # Show first 12 months
            for payment in schedule[:12]:
                self._print_payment_row(payment)
            
            # Show ellipsis
            print(f"{'...':<8} {'...':<12} {'...':<12} {'...':<12} {'...':<12} {'...':<12}")
            
            # Show last 12 months
            for payment in schedule[-12:]:
                self._print_payment_row(payment)
    
    def _print_payment_row(self, payment: Dict):
        """Print a single payment row."""
        print(f"{payment['payment_number']:<8} "
              f"{payment['date']:<12} "
              f"${payment['payment_amount']:<11.2f} "
              f"${payment['principal']:<11.2f} "
              f"${payment['interest']:<11.2f} "
              f"${payment['remaining_balance']:<11.2f}")
    
    def export_to_csv(self, filename: str = None):
        """Export amortization schedule to CSV file."""
        if filename is None:
            filename = f"mortgage_schedule_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        schedule = self.generate_amortization_schedule()
        
        import csv
        with open(filename, 'w', newline='') as csvfile:
            fieldnames = ['payment_number', 'date', 'payment_amount', 'principal', 
                         'interest', 'remaining_balance']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for payment in schedule:
                writer.writerow({
                    'payment_number': payment['payment_number'],
                    'date': payment['date'],
                    'payment_amount': f"{payment['payment_amount']:.2f}",
                    'principal': f"{payment['principal']:.2f}",
                    'interest': f"{payment['interest']:.2f}",
                    'remaining_balance': f"{payment['remaining_balance']:.2f}"
                })
        
        print(f"Amortization schedule exported to: {filename}")


def validate_inputs(principal: float, rate: float, years: int):
    """Validate input parameters."""
    if principal <= 0:
        raise ValueError("Loan amount must be positive")
    if rate < 0:
        raise ValueError("Interest rate cannot be negative")
    if years <= 0:
        raise ValueError("Loan term must be positive")
    if years > 50:
        raise ValueError("Loan term cannot exceed 50 years")


def main():
    """Main function to run the mortgage calculator."""
    parser = argparse.ArgumentParser(description='Calculate mortgage amortization schedule')
    parser.add_argument('principal', type=float, help='Loan amount ($)')
    parser.add_argument('rate', type=float, help='Annual interest rate (%)')
    parser.add_argument('years', type=int, help='Loan term (years)')
    parser.add_argument('--start-date', type=str, help='Start date (YYYY-MM-DD)')
    parser.add_argument('--show-all', action='store_true', help='Show all payments in table')
    parser.add_argument('--export-csv', type=str, help='Export to CSV file')
    parser.add_argument('--summary-only', action='store_true', help='Show only summary')
    
    args = parser.parse_args()
    
    try:
        # Validate inputs
        validate_inputs(args.principal, args.rate, args.years)
        
        # Parse start date if provided
        start_date = None
        if args.start_date:
            try:
                start_date = datetime.strptime(args.start_date, '%Y-%m-%d').date()
            except ValueError:
                print("Error: Invalid start date format. Use YYYY-MM-DD")
                sys.exit(1)
        
        # Create calculator
        calculator = MortgageCalculator(args.principal, args.rate, args.years, start_date)
        
        # Print summary
        calculator.print_summary()
        
        # Print amortization table unless summary-only
        if not args.summary_only:
            calculator.print_amortization_table(args.show_all)
        
        # Export to CSV if requested
        if args.export_csv:
            calculator.export_to_csv(args.export_csv)
    
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Example usage if run without arguments
    if len(sys.argv) == 1:
        print("Mortgage Amortization Calculator")
        print("Usage: python mortgage_calculator.py <principal> <rate> <years>")
        print("\nExample: python mortgage_calculator.py 300000 3.5 30")
        print("\nRunning example calculation...")
        print()
        
        # Run example
        calculator = MortgageCalculator(300000, 3.5, 30)
        calculator.print_summary()
        calculator.print_amortization_table()
    else:
        main()