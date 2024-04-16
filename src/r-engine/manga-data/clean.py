import pandas as pd

def clean_csv(input_file, output_file):
    try:
        with open(input_file, 'r') as f_input:
            lines = f_input.readlines()

        cleaned_lines = []
        for line in lines:
            # Check if the line has the expected number of fields
            if line.count(',') == 11:
                cleaned_lines.append(line)
            else:
                print(f"Irregular line found and skipped: {line}")
                try:
                    with open(input_file, 'r') as f_input:
                        lines = f_input.readlines()

                    cleaned_lines = []
                    for i, line in enumerate(lines):
                        # Split the current line into fields
                        fields = line.strip().split(',')

                        # If the line has fewer fields than expected
                        if len(fields) < 12:
                            # Calculate how many more fields we need
                            needed_fields = 12 - len(fields)

                            # Look for the next line to fill the current line
                            for j in range(i + 1, len(lines)):
                                next_fields = lines[j].strip().split(',')
                                # If the next line has enough fields to fill the current line
                                if len(next_fields) >= needed_fields:
                                    # Add the necessary fields from the next line to the current line
                                    fields.extend(next_fields[:needed_fields])
                                    # Remove the added fields from the next line
                                    lines[j] = ','.join(next_fields[needed_fields:])
                                    break
                                else:
                                    # If the next line doesn't have enough fields, add it to the current line
                                    fields.extend(next_fields)
                                    # Update the number of needed fields
                                    needed_fields = 12 - len(fields)

                        # Join the fields back into a line and append to the cleaned lines
                        cleaned_lines.append(','.join(fields) + '\n')

                    # Write the cleaned lines to the output file
                    with open(output_file, 'w') as f_output:
                        f_output.writelines(cleaned_lines)

                except Exception as e:
                    # Print any errors that occur during processing
                    print("Error:", e)


        # Write the cleaned lines to the output file
        with open(output_file, 'w') as f_output:
            f_output.writelines(cleaned_lines)
    except Exception as e:
        # Print any errors that occur during processing
        print("Error:", e)

# Example usage
input_file = './files/test.csv'
output_file = './files/cleaned_test.csv'
clean_csv(input_file, output_file)
