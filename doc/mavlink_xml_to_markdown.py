#! /usr/bin/python

"""
This script generates markdown files for the MAVLink message definition XML at: 
https://github.com/mavlink/mavlink/tree/master/message_definitions/v1.0
  
The files can be imported into a markdown SSG to display the messages as HTML

The script runs on Python 3. The following libraries must be imported: lxml, requests, bs4.

The file is run in mavlink/doc/ with no arguments. It writes the files to /messages/
It can also be run for a specific dialect, if specified.
It can also be imported and used to get information about the XML.
"""

import lxml.etree as ET
import requests
from bs4 import BeautifulSoup as bs
import re
import os # for walk

import argparse # for command line parsing


class MAVXML(object):
    '''Represents a MAVLink XML file'''
    def __init__(self, filename):
        self.filename = filename
        self.basename = os.path.basename(filename)
        if self.basename.lower().endswith(".xml"):
            self.basename = self.basename[:-4]
        self.basename_upper = self.basename.upper()
        self.messages = []
        self.enums = []
        self.commands = []
        self.includes = []
        self.dialect = None
        self.version = None

        # Read the XML file
        with open(self.filename, 'r') as f:
            xml_content = f.read()
        # Initialize BeautifulSoup with the XML content
        soup = bs(xml_content, 'xml')

        # Extract dialect
        dialect = soup.find('dialect')
        if dialect: self.dialect=dialect.text

        # Extract version
        version = soup.find('version')
        if version: self.version=version.text

        # Extract includes
        includes = soup.find_all('include')
        for include in includes:
            self.includes.append(include.text[:-4])

        # Extract messages
        messages = soup.find_all('message')
        for message in messages:
            self.messages.append(MAVMessage(message))

        # Extact all ENUM except MAV_CMD
        # Define a custom filter function to exclude "MAV_CMD"
        def exclude_mav_cmd(tag):
            return tag.name == 'enum' and tag.get('name') != 'MAV_CMD'
        filtered_enums = soup.find_all(exclude_mav_cmd)
        for enum in filtered_enums:
            self.enums.append(MAVEnum(enum))

        # Extract Commands (MAV_CMD)
        mav_cmd_enum = soup.find('enum', attrs={'name': 'MAV_CMD'})
        if mav_cmd_enum:
            mav_commands = mav_cmd_enum.find_all('entry')
            for command in mav_commands:
                self.commands.append(MAVCommand(command))



    def getMarkdown(self):
        """Generate Markdown for this XML file"""
        markdownText = ""

        # Generate include files docs
        markdownText+="**MAVLink Include Files:**"
        if self.includes:
           base_path = '../messages/'
           # Create a list of formatted strings
           for include in self.includes:
               markdownText+="\n"
               markdownText+=f"\n- [{include}.xml]({base_path}{include}.md)"
        else:
            markdownText+=" None"
        markdownText+="\n\n"

        # Generate dialect and version if present
        if self.dialect: markdownText+=f"**Protocol dialect:** {self.dialect}\n\n"
        if self.version: markdownText+=f"**Protocol version:** {self.version}\n\n"

        if len(self.messages):
            markdownText += "## Messages\n\n"     
        for message in self.messages:
           markdownText += message.getMarkdown()

        if len(self.enums):
            markdownText += "## Enumerated Types\n\n"
        for enum in self.enums:
           markdownText += enum.getMarkdown()

        if len(self.commands):
            markdownText += "## Commands (MAV_CMD) {#mav_commands}\n\n"
        for command in self.commands:
           markdownText += command.getMarkdown()

        return markdownText


class MAVDeprecated(object):
    def __init__(self, soup):
        #name, type, print_format, xml, description='', enum='', display='', units='', instance=False
        self.since = soup.get('since')
        self.replaced_by = soup.get('replaced_by')
        self.description = soup.text

        #self.debug()

    def getMarkdown(self):
        message="**DEPRECATED:**"
        message+=f" Replaced By {fix_add_implicit_links_items(self.replaced_by)} " if self.replaced_by else ''
        message+=f"({self.since})" if self.since else ''
        message+=f" — {self.description})" if self.description else ''
        return message

    def debug(self):
        print(f"debug:Deprecated: since({self.since}), replaced_by({fix_add_implicit_links_items(self.replaced_by)}), description({self.description})")

class MAVWip(object):
    def __init__(self, soup):
        #<wip/>
        self.wip = soup.name

        #self.debug()

    def getMarkdown(self):
        message="**WORK IN PROGRESS**: Do not use in stable production environments (it may change)."
        return message

    def debug(self):
        print(f"debug:WIP: wip({self.wip})")     


class MAVField(object):
    def __init__(self, soup, parent):
        #name, type, print_format, xml, description='', enum='', display='', units='', instance=False
        self.name = soup['name']
        self.type = soup['type']
        #self.name_upper = self.name.upper()
        self.description = soup.contents #may need further processing
        if not self.description:
            self.description = None
            #print(f"DEBUG: field desc not defined: {self.name}")
        elif len(self.description)==1:
            self.description=self.description[0] #Expected
        else :
            print(f"DEBUG: field desc multiple array problem: {self.name} (len: {len(self.description)} )")
            for item in self.description:
                print(f"  DEBUG: {item}")
        self.units = soup.get('units') #may not exist
        self.enum = soup.get('enum') #may not exist
        self.display =  soup.get('display')
        self.print_format = soup.get('print_format')
        self.instance = False
        if soup.get('instance'):
            self.instance = True

        # Tell the message what field types it has - needed for table rendering
        #parent.fieldnames.add('name')
        #parent.fieldnames.add('type')     
        parent.fieldnames.add('description')
        if self.units:
            parent.fieldnames.add('units')
        if self.enum:
            parent.fieldnames.add('enum')
        if self.display:
            parent.fieldnames.add('display')
        if self.print_format:
            parent.fieldnames.add('print_format')
        if self.instance:
            parent.fieldnames.add('instance')

        #self.debug()

    def debug(self):
        print(f"Debug_Field- name ({self.name}), type ({self.type}), desc({self.description}), units({self.units}), display({self.display}), instance({self.instance})")
        # TODO - display, instance, are not output.



class MAVMessage(object):
    def __init__(self, soup):
        self.name = soup['name']
        self.id=int(soup['id'])
        self.name_lower = self.name.lower()
        #self.linenumber = linenumber
        self.description = soup.description.contents #Will do more processing this.
        if len(self.description)==1:
            self.description=self.description[0]
            self.description=tidyDescription(self.description)
            self.description = fix_add_implicit_links_items(self.description)
        else:
            print(f"DEBUG: message desc multiple array problem: {self.name}")

        self.fields = []
        self.fieldnames = set()
        self.deprecated = soup.findChild('deprecated', recursive=False)
        self.deprecated = MAVDeprecated(self.deprecated) if self.deprecated else None
        self.wip = soup.findChild('wip', recursive=False)
        self.wip = MAVWip(self.wip) if self.wip else None

        # TODO: ADD Any other fields of message?

        fields = soup.find_all('field')

        for field in fields:
            self.fields.append(MAVField(field, self))

        #self.debug()

    def getMarkdown(self):
        """
        Return markdown for a message.
        """
        message=f"### {self.name} ({self.id})" + ' {#' + self.name + '}\n\n'

        if self.deprecated:
            message+=self.deprecated.getMarkdown()+"\n\n"
        if self.wip:
            message+=self.wip.getMarkdown()+"\n\n"

        message+=self.description + '\n\n'

        message+='Field Name | Type'
        field_count = 3 # these two + description
        if 'units' in self.fieldnames:
            message+=' | Units'
            field_count+=1
        if 'enum' in self.fieldnames:
            message+=' | Values'
            field_count+=1
        message+=' | Description\n'
        # Generate column marker pattern
        pattern = ("--- | ") * (field_count - 1) + "---\n"
        message+=pattern

        for field in self.fields:
          message+=f"{field.name} | `{field.type}`"

          if 'units' in self.fieldnames:
            message+=f" | {field.units if field.units else ''}"
          if 'enum' in self.fieldnames:
            message+=f" | {fix_add_implicit_links_items(field.enum) if field.enum else ''}"
            #markdownText = fix_add_implicit_links_items(field.enum)
          message+= f" | {fix_add_implicit_links_items(tidyDescription(field.description,'table'))}\n" if field.description else '| \n'

        message+="\n"         
        return message
        
    def debug(self):
        print(f"debug:message: name({self.name}, id({self.id}), description({self.description}), deprecated({self.deprecated})")

class MAVEnumEntry(object):
    def __init__(self, soup):
        #name, value, description='', end_marker=False, autovalue=False, origin_file='', origin_line=0, has_location=False
        self.name = soup['name']
        self.value = soup.get('value') if soup.get('value') else print(f"TODO MISSING VALUE in ENUMentry: {self.name}")
        self.description = soup.findChild('description', recursive=False)
        self.description = self.description.text if self.description else None
        self.deprecated = soup.findChild('deprecated', recursive=False)
        self.deprecated = MAVDeprecated(self.deprecated) if self.deprecated else None
        self.wip = soup.findChild('wip', recursive=False)
        self.wip = MAVWip(self.wip) if self.wip else None
        #self.autovalue = autovalue  # True if value was *not* specified in XML

    def getMarkdown(self):
        """Return markdown for an enum entry"""
        deprString=f"<b>{self.deprecated.getMarkdown()}" if self.deprecated else ""
        if self.wip: print(f"TODO: WIP in Enum Entry: {self.name}")
        desc = fix_add_implicit_links_items(tidyDescription(self.description,'table')) if self.description else ""
        string = f"<a id='{self.name}'></a>{self.value} | [{self.name}](#{self.name}) | {desc}{deprString}\n"
        return string


class MAVEnum(object):
    def __init__(self, soup):
        #name, linenumber, description='', bitmask=False
        self.name = soup['name']     
        self.entries = []
        self.description = soup.findChild('description', recursive=False)
        self.description = tidyDescription(self.description.text) if self.description else None
        self.deprecated = soup.findChild('deprecated', recursive=False)
        self.deprecated = MAVDeprecated(self.deprecated) if self.deprecated else None
        self.wip = soup.findChild('wip', recursive=False)
        self.wip = MAVWip(self.wip) if self.wip else None
        self.bitmask = soup.get('bitmask')
        enumEntries = soup.find_all('entry')
        for entry in enumEntries:
            self.entries.append(MAVEnumEntry(entry))

    def getMarkdown(self):
        """Return markdown for a whole enum"""
        string = f"### {self.name}" + " {#" + f"{self.name}" + "}\n\n"
        if self.deprecated:
            string+=self.deprecated.getMarkdown()+"\n\n"

        if self.wip:
            string+=self.wip.getMarkdown() + "\n\n"
        
        #if self.name=="MAV_FRAME":
        #    pass
        #    self.debug()

        string += "(Bitmask) " if self.bitmask else ""
        string += f"{fix_add_implicit_links_items(self.description)}" if self.description else ""
        if self.bitmask or self.description: string += "\n\n"
        string += "Value | Field Name | Description\n--- | --- | ---\n"
        for entry in self.entries:
            string += entry.getMarkdown()
        string +="\n"

        return string

    def debug(self):
        print(f"debug:MAVEnum: name({self.name}), bitmask({self.bitmask}), deprecated({self.deprecated}) ")


class MAVCommandParam(object):
    def __init__(self, soup, parent):
        #name, value, description='', end_marker=False, autovalue=False, origin_file='', origin_line=0, has_location=False
        pass
        self.index = soup['index']
        self.label = soup.get('label')
        self.units = soup.get('units')
        self.minValue = soup.get('minValue')
        self.maxValue = soup.get('maxValue')
        self.increment = soup.get('increment')
        self.enum = soup.get('enum')
        self.description = soup.text if soup.text else None
        if self.description: self.description=tidyDescription(self.description,"table")
        #no deprecated or wip supported
        #self.autovalue = autovalue  # True if value was *not* specified in XML

        # Add fields to display in parent.
        parent.param_fieldnames.add('index')
        if self.label: parent.param_fieldnames.add('label')
        if self.units: parent.param_fieldnames.add('units')
        if self.minValue: parent.param_fieldnames.add('minValue')
        if self.maxValue: parent.param_fieldnames.add('maxValue')
        if self.increment: parent.param_fieldnames.add('increment')
        if self.enum: parent.param_fieldnames.add('enum')

class MAVCommand(object):
    def __init__(self, soup):
        #name, value, description='', end_marker=False, autovalue=False, origin_file='', origin_line=0, has_location=False
        pass
        self.name = soup['name']
        self.value = soup.get('value') if soup.get('value') else "TODO MISSING VALUE"
        self.description = soup.description.text if soup.description else None
        if self.description: self.description=tidyDescription(self.description)
        self.deprecated = soup.findChild('deprecated', recursive=False)
        self.deprecated = MAVDeprecated(self.deprecated) if self.deprecated else None
        self.wip = soup.findChild('wip', recursive=False)
        self.wip = MAVWip(self.wip) if self.wip else None
        #self.autovalue = autovalue  # True if value was *not* specified in XML
        self.param_fieldnames = set()
        self.params = []
        params = soup.find_all('param')
        for param in params:
            self.params.append(MAVCommandParam(param, self))


    def getMarkdown(self):
        """Return markdown for a command (entry)"""
        string = f"### {self.name}" + " {#" + f"{self.name}" + "}\n\n"
        if self.deprecated:
            string+=self.deprecated.getMarkdown() + "\n\n"
        if self.wip:
            string+=self.wip.getMarkdown() + "\n\n"

        string += f"{fix_add_implicit_links_items(self.description)}\n\n" if self.description else ""
        tableHeadings = []
        tableHeadings.append('Param (Label)')
        tableHeadings.append('Description')
        valueHeading = False
        unitsHeading = False
        if any(field in self.param_fieldnames for field in ('enum', 'minValue', 'maxValue', 'increment')):
            valueHeading = True
            tableHeadings.append('Values')
        if 'units' in self.param_fieldnames:
            unitsHeading = True
            tableHeadings.append('Units')
        tableRows = []
        
        for param in self.params:
          row=[] 
          row.append(f"{param.index} ({param.label})" if param.label else param.index)
          row.append(param.description if param.description else "")

          if valueHeading:
            valString=" "
            if param.enum:
                valString=fix_add_implicit_links_items(param.enum)
            elif param.minValue or param.maxValue or param.increment:
                if param.minValue: valString+=f"min: {param.minValue}"
                if param.maxValue: valString+=f" min: {param.maxValue}"
                if param.maxValue: valString+=f" inc: {param.increment}"
                valString = valString.strip()
            row.append(valString)

          if unitsHeading:
            unitsString=" "
            if param.units:
               unitsString = param.units
            row.append(unitsString)
        
          tableRows.append(row)

          
          #print(tableRows)
        string += generateMarkdownTable(tableHeadings, tableRows)
        string+="\n\n"        

        return string

def tidyDescription(desc_string, type="markdown"):
    """
    Helper method to remove odd whitepace etc from a description string.
    Different behaviour if the string is to be used in normal markdown or in a table.
    """
    if "\n" not in desc_string:
        desc_string = desc_string.strip()
        #print(f"debug1strp|{desc_string}|")
        return desc_string
    if type=="markdown":
        #print(f"debug2|{desc_string}|")
        desc = desc_string
        desc.strip()
        lines = desc.splitlines()
        first_line = lines[0].strip()
        new_string = first_line + "\n\n"
        for line in lines[1:]:
            new_string += line.strip() + "\n"
        desc_string=new_string.strip()
        #print(f"debug3|{desc_string}|")   
        return desc_string
    if type=="table":
        lines = desc_string.strip().splitlines()
        new_string="<br>".join(line.strip() for line in lines)
        #for line in lines:
        #    new_string += line.strip() + "<br>"

        return new_string.strip()
        
def fix_add_implicit_links_items(input_text):
    if not type(input_text) is str:
        # Its not something we can handle
        return input_text

    # Makes screaming snake case into anchors (helper method). Special fix for MAV_CMD.
    # I don't remember this regexp but it appears to work
    # print("fix_add_implicit_link was called")
    def make_text_to_link(matchobj):
        #print("make_entry_to_link was called: %s" % matchobj.group(0))
        item_string = matchobj.group(2)
        item_url=item_string
        if item_string == 'MAV_CMD':
            item_url='mav_commands'
        returnString = f"{matchobj.group(1)}[{item_string}](#{item_url}){matchobj.group(3)}"
        return returnString
    
    linked_md=re.sub(r'([\`\(\s,]|^)([A-Z]{2,}(?:_[A-Z0-9]+)+)([\`\)\s\.,:]|$)', make_text_to_link, input_text,flags=re.DOTALL)
    return linked_md

def generateMarkdownTable(headings, rows):
    """Generates a markdown table from an array containing headings and array containing array for every row."""
    string = ""
    pattern = " | ".join(headings) + "\n"
    string+=pattern
    # Generate column marker pattern
    field_count=len(headings)
    pattern = ("--- | ") * (field_count - 1) + "---\n"
    string+=pattern
    for row in rows:
        #print('debug: ROW:')
        #print(row)
        pattern = " | ".join(row) + "\n"
        string+=pattern
    return string


def main():
    parser = argparse.ArgumentParser(description="Markdown Generator for MAVLink Docs from XML")

    parser.add_argument("-d", "--source_dir", default="../message_definitions/v1.0/", help="Path to XML definition directory")  
    parser.add_argument("-i", "--input_dialect", default = None, help="Name of XML dialect, e.g. 'common' (if not specified, does all dialects)")
    parser.add_argument("-o","--output", default = "./messages/", help="Path to Markdown output directory")
    args = parser.parse_args()
    #print(args.source_dir)
    #print(args.input_dialect)
    #print(args.output)

    xml_dialects = [] #The list of dialects to generate markdown for
    if args.input_dialect:
        xml_dialects.append(args.input_dialect) 
    else:
        all_files = os.listdir(args.source_dir)
        xml_dialects = [file[:-4] for file in all_files if file.endswith('.xml')]
        #xml_dialects.append(f"{args.source_dir}{args.input_dialect}.xml")
    #print(xml_dialects)

    
    for dialect in xml_dialects:
        xmlFileName= f"{args.source_dir}{dialect}.xml"
        print(f"Processing: {xmlFileName}")
        xmlParser = MAVXML(xmlFileName)
        xmlString=xmlParser.getMarkdown()

        #Create outputdir if it does not exist
        if not os.path.exists(args.output):
          os.makedirs(args.output)

        output_file = f"{args.output}{dialect}.md"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(xmlString)

if __name__ == "__main__":
    main()



