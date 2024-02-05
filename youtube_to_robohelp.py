import json
import logging
import os
import xml.etree.ElementTree as ET
from xml.dom import minidom
import scrapetube
from youtube_transcript_api import YouTubeTranscriptApi
import openai
from openai import OpenAI
import unicodedata
import re
from time import time
import os


class YouTubeVideo:
    """
    Represents a YouTube video.
    """

    def __init__(self, video_id, title, url, embed_url, description, thumbnail_url, thumbnail_width, thumbnail_height, html_filename):
        self.video_id = video_id
        self.title = title
        self.url = url
        self.embed_url = embed_url
        self.description = description
        self.thumbnail_url = thumbnail_url
        self.thumbnail_width = thumbnail_width
        self.thumbnail_height = thumbnail_height
        self.html_filename = html_filename

    def to_dict(self):
        """
        Converts the YouTubeVideo object to a dictionary.
        Returns:
            dict: A dictionary representation of the YouTubeVideo object.
        """
        return {
            "video_id": self.video_id,
            "title": self.title,
            "url": self.url,
            "embed_url": self.embed_url,
            "description": self.description,
            "thumbnail_url": self.thumbnail_url,
            "thumbnail_width": self.thumbnail_width,
            "thumbnail_height": self.thumbnail_height,
            "html_filename": self.html_filename
        }

    @classmethod
    def load_from_scrapetube_data(cls, video_data):
        """
        Creates a YouTubeVideo object from the provided video data.
        Args:
            video_data (dict): The video data.
        Returns:
            YouTubeVideo: A YouTubeVideo object created from the video data.
        Raises:
            ValueError: If there is missing or incorrect data in the video_data.
        """
        try:
            video_id = video_data['videoId']
            title = video_data['title']['runs'][0]['text']
            url = f"https://www.youtube.com/watch?v={video_id}"
            embed_url= f"https://www.youtube.com/embed/{video_id}"

            # Handle cases where 'descriptionSnippet' might be missing or not have 'runs'
            if 'descriptionSnippet' in video_data and 'runs' in video_data['descriptionSnippet'] and video_data['descriptionSnippet']['runs']:
                description = video_data['descriptionSnippet']['runs'][0]['text']
                description = description.split('\n')[0]  # Extracting the first part before '\n'
            else:
                description = "No description available."

            # Safely accessing thumbnail data
            thumbnail = video_data.get('thumbnail', {}).get('thumbnails', [{}])[1]
            thumbnail_url = thumbnail.get('url', "No thumbnail URL.")
            thumbnail_width = thumbnail.get('width', 0)
            thumbnail_height = thumbnail.get('height', 0)
            html_filename = ""

            return cls(video_id, title, url, embed_url, description, thumbnail_url, thumbnail_width, thumbnail_height, html_filename)
        except KeyError as e:
            # Handle missing data in video_data
            raise ValueError(f"Key {e} missing in video data. Cannot create YouTubeVideo object.") from e
        except IndexError as e:
            # Handle incorrect index access in lists
            raise ValueError(f"Index error in video data. Cannot create YouTubeVideo object.") from e
        except Exception as e:
            # Handle any other unforeseen exceptions
            raise ValueError(f"An error occurred when creating a YouTubeVideo object: {e}") from e

class TranscriptEnhancer:
    """
    A class that enhances video transcripts by correcting errors, formatting them into chapters,
    and converting them to HTML format.
    """
    def __init__(self, api_key):
        self.openai_client = OpenAI()
        self.openai_client.api_key = api_key

    def _save_file(self, filepath, content):
        with open(filepath, 'w', encoding='utf-8') as outfile:
            outfile.write(content)

    def json_to_html(self, json_str):
        """
        Converts a JSON string to HTML format.
        """
        chapters = json.loads(json_str)
        html_output = ""

        for chapter in chapters:
            title = chapter["title"]
            content = chapter["content"]
            html_output += f"<p><strong>{title}</strong><br/>\n\t{content}</p>\n"

        return html_output

    def enhance_transcript(self, transcript, base_name="", model="gpt-3.5-turbo"):
        """
        Enhances the given transcript by correcting errors, formatting it into chapters,
        and converting it to HTML format.
        The prompt is in french since the transcript is in french itself.
        """
        messages = [
            {
                "role": "system",
                "content": "Je vais te donner un texte qui est la transcription d'une vidéo.\n"
                "Voici ta tâche : \n"
                "* Corrige les éventuelles erreurs de transcription, tout en conservant le texte correct inchangé.\n"
                "* Remets en forme ce texte, sous forme de chapitres.\n"
                "* Ajoute un titre aux chapitres, sans le préfixer de 'Chapitre n:', ni d'un numéro de chapitre\n"
                "* ajoute des sauts de ligne pour améliorer la lisibilité\n"
                "Retourne juste le texte au format HTML, sans rien ajouter, sous le modèle suivant :\n"
                "<p><strong>titre_chapitre_1</strong><br/>\n"
                "    texte_chapitre_1</p>\n"
                "<p><strong>titre_chapitre_2</strong><br/>\n"
                "    texte_chapitre_2</p>\n"
                "...\n"
                "Transcription :\n" + transcript
            },
        ]

        try:
            response = self.openai_client.chat.completions.create(
                model=model,
                messages=messages,
            )

            enhanced_transcript = response.choices[0].message.content
            # fix small defaults
            enhanced_transcript = enhanced_transcript.replace('</p> <p>', '</p>\n<p>')

            prompt = messages[0]['content']
            filename = '%s_gpt3.txt' % time()
            self._save_file('gpt3_logs/%s' % filename, prompt + '\n\n==========\n\n' + enhanced_transcript)

            if (base_name != ""):
                if not os.path.exists('improved'):
                    os.makedirs('improved')
                self._save_file(f'improved/{base_name}', enhanced_transcript)

            return enhanced_transcript
        except Exception as e:
            print(f"GPT-3 API error: {e}")
            return None

    def get_existing_enhanced_transcript(self, base_name):
        """
        Retrieves an existing enhanced transcript from a file.
        """
        transcript_file = f"improved/{base_name}"
        if os.path.exists(transcript_file):
            with open(transcript_file, 'r', encoding='utf-8') as file:
                return file.read()
        else:
            return None

        
class TOCManager:
    """
    A class that manages the .toc xml file that includes all files in robohelp content .
    """
    def __init__(self, toc_file):
        self.toc_file = toc_file

    def is_video_listed(self, video_html_filename):
        tree = ET.parse(self.toc_file)
        root = tree.getroot()
        for page in root.findall('.//page'):
            if page.get('href').endswith(video_html_filename):
                return True
        return False

    def add_video(self, video_html_filename):
        tree = ET.parse(self.toc_file)
        root = tree.getroot()
        ET.SubElement(root, "page", href="../contents/" + video_html_filename)
        self.pretty_print_and_write_xml(root)

    def pretty_print_and_write_xml(self, element):
        # Convert the ElementTree to a string and parse it with minidom
        xml_string = ET.tostring(element, 'utf-8')
        parsed_string = minidom.parseString(xml_string)

        # Use minidom's pretty-printing functionality
#        pretty_xml_as_string = parsed_string.toprettyxml(indent="  ")
        pretty_xml_as_string = parsed_string.toprettyxml(indent="\t", newl="\n", encoding="utf-8").decode('utf-8')

        # Normalize line endings to '\n' and remove extra line feeds
        pretty_xml_as_string = pretty_xml_as_string.replace('\r\n', '\n')
        pretty_xml_as_string = '\n'.join([s for s in pretty_xml_as_string.split('\n') if s.strip()])

        # Write the formatted string back to the file
        with open(self.toc_file, 'w', encoding='utf-8') as file:
            file.write(pretty_xml_as_string)
            
class HTMLGenerator:
    """
    Generates the content of a HTML page for oney video .
    """
    def __init__(self, template_path):
        self.template_path = template_path

    def _load_template(self):
        with open(self.template_path, 'r', encoding='utf-8') as file:
            return file.read()

    def generate_html(self, video, enhanced_transcript):
        template = self._load_template()
        html_content = template.replace('###thumbnail_url###', video.thumbnail_url)
        html_content = html_content.replace('###video_name###', video.title)
        html_content = html_content.replace('###video_url###', video.embed_url)
        html_content = html_content.replace('###video_description###', video.description)
        html_content = html_content.replace('###enhanced_transcript###', enhanced_transcript)
        return html_content


class VideoProcessor:
    """
    Manages the full process of processing one YT video ands adding it to the help content .
    """
    def __init__(self, toc_manager, transcript_enhancer, html_generator, transcript_dir, html_dir):
        # Initialize VideoProcessor object with necessary components
        self.toc_manager = toc_manager
        self.transcript_enhancer = transcript_enhancer
        self.html_generator = html_generator
        self.transcript_dir = transcript_dir
        self.html_dir = html_dir

    def process_video(self, video, force_enhancement=True):
        try:
            # Normalize the unicode string to decompose the accented characters
            normalized_title = unicodedata.normalize('NFKD', video.title)
            # Encode the string to ASCII bytes, then decode back to string ignoring errors
            ascii_title = normalized_title.encode('ASCII', 'ignore').decode('ASCII')
            # Replace spaces with underscores and make lowercase for the filename
            ascii_title = re.sub(r'\s+', '_', ascii_title).lower()
            video.html_filename = ascii_title + '.htm'
            if not self.toc_manager.is_video_listed(video.html_filename):
                # Get the transcript of the video
                transcript = YouTubeTranscriptApi.get_transcript(video.video_id, languages=('fr',))
                # Convert the transcript to a single string
                text = ' '.join([i['text'] for i in transcript])
                # Remove the '[Musique]' texts from the transcript
                text = text.replace('[Musique]', '')
                enhanced_file_name = ascii_title + '-transcript.txt'
                enhanced_transcript = None
                if (force_enhancement == False):
                    # Check if enhanced transcript already exists
                    enhanced_transcript = self.transcript_enhancer.get_existing_enhanced_transcript(enhanced_file_name)
                if (enhanced_transcript == None):
                    # Enhance the transcript if not already enhanced
                    enhanced_transcript = self.transcript_enhancer.enhance_transcript(text, base_name = enhanced_file_name, model = "gpt-4")
                # Generate HTML content using the video and enhanced transcript
                html_content = self.html_generator.generate_html(video, enhanced_transcript)
                # Save the HTML content to a file
                self._save_file(os.path.join(self.html_dir, video.html_filename), html_content)
                # Add the video to the table of contents
                self.toc_manager.add_video(video.html_filename)
        except Exception as e:
            # Log the error to a file
            logging.basicConfig(filename='error.log', level=logging.ERROR)
            logging.error(f"An error occurred: {str(e)}")
            # Exit the method
            return
    def _save_file(self, filepath, content):
        with open(filepath, 'w', encoding='utf-8') as outfile:
            outfile.write(content)

# Get the current working directory
current_directory = os.getcwd()

# Initialize the components
# Get the current working directory
current_directory = os.getcwd()

# Convert relative paths to absolute paths
toc_file_path = os.path.abspath(os.path.join(current_directory, 'Videos', 'toc', 'Default.toc'))
video_list_file_path = os.path.abspath(os.path.join(current_directory, 'video_data.json'))
html_template_path = os.path.abspath(os.path.join(current_directory, 'Videos', 'youtube_template', 'video_template.htm'))
html_output_path = os.path.abspath(os.path.join(current_directory, 'Videos', 'contents'))
path_to_transcripts = os.path.abspath(os.path.join(current_directory, 'transcripts'))

with open(os.path.join(current_directory, 'key_openai.txt'), 'r') as file:
    openai_api_key = file.read().strip()

# Initialize objects with absolute paths
toc_manager = TOCManager(toc_file_path)
transcript_enhancer = TranscriptEnhancer(openai_api_key)
html_generator = HTMLGenerator(html_template_path)

video_processor = VideoProcessor(toc_manager, transcript_enhancer, html_generator, path_to_transcripts, html_output_path)

video_list = []

# Process each video
channel_id = 'UCEwkL7_F9fob_wOIRBuRL6Q'
videos = scrapetube.get_channel(channel_id)
for video_data in videos:
    video = YouTubeVideo.load_from_scrapetube_data(video_data)
    video_processor.process_video(video, force_enhancement=True)
    video_list.append(video.to_dict())
#    if len(video_list) > 20:
#       break

with open(video_list_file_path, 'w', encoding='utf-8') as file:
    json.dump(video_list, file, ensure_ascii=False, indent=4)

print("Processing complete.")


