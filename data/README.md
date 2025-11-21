# Data Directory

Place your `mongodb_docs.json` file in this directory.

The data file should be a JSON array of documents with the following structure:

```json
[
  {
    "updated": "2024-05-20T17:30:49.148Z",
    "metadata": {
      "contentType": null,
      "productName": "MongoDB Atlas",
      "tags": ["atlas", "docs"],
      "version": null
    },
    "action": "created",
    "sourceName": "snooty-cloud-docs",
    "body": "# Document Title\n\nDocument content goes here...",
    "url": "https://mongodb.com/docs/...",
    "format": "md",
    "title": "Document Title"
  }
]
```

## Required Fields

- `body`: The text content to be chunked and embedded (required)
- Other fields are optional but will be preserved in the embedded documents

## Getting the Data

If you're following the MongoDB AI RAG Lab, the data file should be provided as part of the workshop materials.

Otherwise, you can create your own JSON file following the structure above.

