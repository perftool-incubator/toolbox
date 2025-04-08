#!/bin/python3

import sys

"""
Converts a comma-separated string of CPU numbers into a compressed range
format.
- Removes duplicates
- Sorts numbers
- Creates optimal ranges
- Rejects negative numbers
Example: "1,2,10,11,3,4,5,6,4,4,3" ==> "1-6,10-11"
"""


def cpus_to_ranges(cpu_list):

    try:
        # Split input and convert to integers
        numbers = list(map(int, cpu_list.split(',')))

        # Validate input - no negative numbers allowed
        if any(num < 0 for num in numbers):
            raise ValueError("Negative numbers are not allowed")
            
        # Remove duplicates and sort
        numbers = sorted(set(numbers))

        # Handle empty input scenario
        if not numbers:
            return ""
   
        # Initialize range tracking
        ranges = []
        start = prev = numbers[0]
    
        # Detect consecutive ranges
        for num in numbers[1:]:
            if num == prev + 1:
                # Contiguous, current number continues the sequence
                prev = num
            else:
                # Sequence is broken, save the current range
                if start == prev:
                    ranges.append(str(start))  # Single number
                else:
                    ranges.append(f"{start}-{prev}") # Save the actual range
                # Start a new potential range
                start = prev = num
    
        # Add the last range after loop completes
        if start == prev:
            ranges.append(str(start))  # Single number at end
        else:
            ranges.append(f"{start}-{prev}")  # Final range
   
        # Join all ranges with commas
        return ','.join(ranges)

    except ValueError as e:
        return f"Error: {str(e)}"


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 cpurange.py <comma_separated_cpu_list>")
        print("Example: python3 cpurange.py 1,2,3,4,5,10,11,12")
        sys.exit(0)
    
    # Comma-separated cpus input comes from command line argument
    input_cpus = sys.argv[1]
    output_ranges = cpus_to_ranges(input_cpus)
    print(output_ranges)
    sys.exit(0)
