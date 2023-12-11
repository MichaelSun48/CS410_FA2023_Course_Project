# A Different Approach to Notion Search


## Team Members
* Michael Sun (Captain)
* Maxwell Wang 

## Introduction 
For our CS410 course project, we present a different approach to Notion Search. Notion is a innovative all-in one productivity tool that includes a rich-text note taking feature. Both of us  use Notion as our primary note taking tool, and while we enjoy the features and rich text capabilities, both of us thought that Notion's serach functionality was lacking. 

That is why we decided to apply what we learned in CS410 to Notion by creating a different appraoch to Notion search. Our version is built from scratch using only built-in python libraries and implements the OkapiBM25 scoring function discussed in class, but we have also leveraged Notion's rich text capabilties to incorporate Notion-sepcific heuristics into our scoring function. This means that we can, say, weight **bolded** text more, or weight ~~strikethrough~~ text less, and much more 

## Installation and Setup 

To run our project, you will gather the links of all the Notion pages you'd like to search through, and connect each them to a custom Notion integration. The official guide for how to do this can be found [here](https://developers.notion.com/docs/create-a-notion-integration), but here is high level guide for how to do this:

1. Navigate to your [Notion integrations page](https://www.notion.com/my-integrations](https://www.notion.com/my-integrations))
2. Name and create a new integration, and jot down the Secret key that is presented
3. Go to a Notion page, click `•••` at the top right, and at the very bottom click `Add connections`.
4. You should see the name of the integration you just created as an option. Click it.

To avoid having to add each page to your integration separately, we recommend that you nest all the page in your Notion corpus into one parent page, then simply add this one parent to your integration. This will automatically apply the integration to all nested paged. 

Now, simply clone our repository and navigate to the `main.py` file in the root of this GitHub repository. Input the links to the Notion pages you wish to search through into the `notion_page_urls` list and input the Secret key you obtained from step 2 into the `NotionSearch` object. Finally, navigate to this directory in your command line, and type `python3 main.py`. 

## Assignment Submissions
* Our initial Project Proposal can be found in our GitHub Repository. It is titled CS 410 Project Proposal 
* Our initial Project Proposal can be found in our GitHub Repository. It is titled CS 410 Project Update 
* The bulk of our source code can be found under the `scripts` directory in the `IVIndex.py` and `NotionSearch.py` files. 
* Our video submission can be found at [this](https://drive.google.com/file/d/11S045CpQf4fbI_ZHwPuZMcJWBqiuiN6o/view?usp=drive_link)  Google drive link 

