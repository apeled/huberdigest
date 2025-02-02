# TLDhubeR

Welcome to **TLDhubeR**, a project focused on retrieving and presenting information from Andrew Huberman’s podcasts, utilizing data from Andrew Huberman's RSS feed and podcast transcripts sourced from YouTube. Our application allows you to explore the topics covered in Huberman’s podcasts and offers a direct line to ask and learn about topics he discusses.

Check out the /examples/README.md to learn how to set up the application locally!

## Getting Started

### Step 1: API Key Configuration

![API Key Configuration Image](../tldhuber/static/api_key.png)

Before chatting with Andrew Huberman, you'll need to obtain an OpenAI API key. If you already have one, enter it into the designated field in the side page and press 'Enter'. If you do not have one, click on the `Get an OpenAI API key` and follow the instructions on the OpenAI webpage. API calls generated by our app should cost less than one cent per call.

### Step 2: Loading the Index

![Index Loading Image](../tldhuber/static/load_index.png)

After entering your API key, the index will begin to load. This process can take anywhere from 30 to 60 seconds. During this time, our application is preparing the vector database that includes Andrew Huberman’s podcast transcripts and metadata.

### Step 3: Chat with Andrew Huberman

![Chat Interface Image](../tldhuber/static/chat_interface.png)

![Chat Example Image](../tldhuber/static/chat_example.png)

Now that everything is set up, you can use the chat interface to ask questions or explore topics of interest. For example, try asking about sleep, a common topic of Huberman's podcasts. A chat response from Andrew will appear, as well as an embedded YouTube video that is relevant to the search.
