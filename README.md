# ig-mbs-scheduler

A tool for scraping saved posts from Instagram, and scheduling them on Meta Business Suite.

## Installation

```
git clone git@github.com:adamdorogi/ig-mbs-scheduler.git
cd ig-mbs-scheduler
pip install .
```

## Setup

### Instagram collections

Posts should be saved to Instagram collections with names in the following format:

> \<story\>,\<hashtags\>,\<caption\>

Where:

- "story" is a flag indicating whether to repost the item(s) in this collection as a story. The value "y" will evaluate to true, any other value will evaluate to false. If true, "hashtags" and "caption" will be ignored.
- "hashtags" is a flag indicating whether to reuse the hashtags from the saved items in this collection. The value "y" will evaluate to true, any other value will evaluate to false. If false, the hashtags provided through the CLI's `--hashtags` options will be used.
- "caption" is a string of text to be used as the new caption. If empty, the caption of the original post will be used.

### Caption template

The `--caption-template` option of the CLI supports three format variables:

- {caption}
  - The caption as specified in [Instagram collections](#instagram-collections).
- {hashtags}
  - The hashtags as specified in [Instagram collections](#instagram-collections).
- {user}
  - The user of the original post.
