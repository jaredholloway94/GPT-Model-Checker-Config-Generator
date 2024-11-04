from openai import OpenAI
import uuid, re, json, os, datetime
import xml.etree.ElementTree as ET

client = OpenAI()

def get_model_checker_config(user_prompt):
    model_checker_config_schema = {
        "type": "object",
        "properties": {
            "MCSettings": {
                "type": "object",
                "properties": {
                    "AllowRequired": {"type": "string", "enum": ["True", "False"]},
                    "Name": {"type": "string"},
                    "Author": {"type": "string"},
                    "Description": {"type": "string"},
                    "Image": {"type": "string"},
                    "LastModified": {"type": "string", "format": "date-time"},
                    "Heading": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "ID": {"type": "string"},
                                "HeadingText": {"type": "string"},
                                "Description": {"type": "string"},
                                "IsChecked": {"type": "string", "enum": ["True", "False"]},
                                "Section": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "ID": {"type": "string"},
                                            "SectionName": {"type": "string"},
                                            "Title": {"type": "string"},
                                            "Description": {"type": "string"},
                                            "IsChecked": {"type": "string", "enum": ["True", "False"]},
                                            "Check": {
                                                "type": "array",
                                                "items": {
                                                    "type": "object",
                                                    "properties": {
                                                        "ID": {"type": "string"},
                                                        "CheckName": {"type": "string"},
                                                        "Description": {"type": "string"},
                                                        "FailureMessage": {"type": "string"},
                                                        "ResultCondition": {"type": "string", "enum": ["FailNoElements", "FailMatchingElements", "CountOnly", "CountAndList"]},
                                                        "CheckType": {"type": "string", "enum": ["Custom"]},
                                                        "IsRequired": {"type": "string", "enum": ["True", "False"]},
                                                        "IsChecked": {"type": "string", "enum": ["True", "False"]},
                                                        "Filter": {
                                                            "type": "array",
                                                            "items": {
                                                                "type": "object",
                                                                "properties": {
                                                                    "ID": {"type": "string"},
                                                                    "Operator": {"type": "string", "enum": ["And", "Or", "Exclude"]},
                                                                    "Category": {"type": "string", "enum": ["APIParameter", "APIType", "Category", "DesignOption", "Family", "Host", "HostParameter", "Level", "Parameter", "PhaseCreated", "PhaseDemolished", "PhaseStatus", "Redundant", "Room", "Space", "StructuralType", "Type", "TypeorInstance", "View", "Workset"]},
                                                                    "Property": {"type": "string", "enum": ["Elevation", "Full Class Name", "Is Defined", "Is Element Type", "Is In-Place", "Location", "Name", "Value", "OST Family Categories", "Parameter Names"]},
                                                                    "Condition": {"type": "string", "enum": ["Included", "Equal", "NotEqual", "GreaterThan", "LessThan", "GreaterOrEqual", "LessOrEqual", "Contains", "DoesNotContain", "Defined", "Undefined", "HasValue", "HasNoValue", "Duplicated", "MatchesParameter", "DoesNotMatchParameter", "WildCard", "WildCardNoMatch"]},
                                                                    "Value": {"type": "string"},
                                                                    "CaseInsensitive": {"type": "string", "enum": ["True", "False"]},
                                                                    "Unit": {"type": "string", "enum": ["Default", "Inches", "Feet", "Millimeters", "Centimeters", "Meters"]},
                                                                    "UnitClass": {"type": "string", "enum": ["None", "Length", "Area", "Volume", "Angle"]},
                                                                    "FieldTitle": {"type": "string"},
                                                                    "UserDefined": {"type": "string", "enum": ["True", "False"]},
                                                                    "Validation": {"type": "string", "enum": ["None", "Boolean", "Integer", "Length"]}
                                                                }
                                                            }
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "required": ["AllowRequired", "Name", "Author", "Headings"]
            }
        }
    }
    messages = [
        {
            "role": "system",
            "content": "You are a Revit modeling expert. Use the provided schema to generate valid model checker configurations."
        },
        {
            "role": "user",
            "content": user_prompt
        }
    ]
    response_format = {
        "type": "json_schema",
        "json_schema": {
            "name" :"model_checker_config_schema",
            "schema": model_checker_config_schema
        }
    }
    response = client.chat.completions.create(
        model = "gpt-4o-2024-08-06",
        messages = messages,
        response_format = response_format
    )
    return response.choices[0].message.content


def clean_mc_str(mc_str):
    # replace IDs with uuids
    def replace_with_uuid(match):
        return str(uuid.uuid4())
    mc_str = re.sub(
        r'(?<="ID":")[^"]+(?=")',
        replace_with_uuid,
        mc_str
    )
    # replace yyyy-mm-dd with Windows Filetime format
    def replace_with_windows_datetime(match):
        delta = datetime.datetime.now() - datetime.datetime(1601, 1, 1, 0, 0, 0)
        return str(int(delta.total_seconds() * 10**7))
    mc_str = re.sub(
        r'(?<="LastModified":")[^"]+(?=")',
        replace_with_windows_datetime,
        mc_str
    )
    return mc_str


def save_json_to_xml(json_data, filename=f"{str(uuid.uuid4())}-model_checker_config.xml"):
    """
    Converts JSON data to XML format with attributes and saves it to a specified file.
    
    Parameters:
        json_data (dict): The JSON data to convert.
        filename (str): The name of the output XML file.
    """
    def build_xml_element(data, parent_element, use_attributes=False):
        for key, value in data.items():
            if isinstance(value, dict):
                # Create a child element with attributes if `use_attributes` is True
                child = ET.SubElement(parent_element, key)
                build_xml_element(value, child, use_attributes=True)
            elif isinstance(value, list):
                # Handle list items as nested elements
                for item in value:
                    item_element = ET.SubElement(parent_element, key)
                    build_xml_element(item, item_element, use_attributes=True)
            else:
                if use_attributes:
                    # Assign simple values as attributes instead of child elements
                    parent_element.set(key, str(value))
                else:
                    # Default behavior for non-attribute elements
                    child = ET.SubElement(parent_element, key)
                    child.text = str(value)

    # Create the root element
    root = ET.Element("MCSettings")
    # Populate the XML structure based on JSON data with root-level attributes
    build_xml_element(json_data["MCSettings"], root, use_attributes=True)

    # Write the XML to a file
    tree = ET.ElementTree(root)
    tree.write(filename, encoding="utf-8", xml_declaration=True)
    print(f"XML file saved as {os.getcwd()}\{filename}")


mc_str = get_model_checker_config(input("Enter your model checker config prompt:\n\n"))
mc_json = json.loads(clean_mc_str(mc_str))
save_json_to_xml(mc_json)