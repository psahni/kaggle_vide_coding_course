#!/usr/bin/env node

import Parser from 'rss-parser';
import minimist from 'minimist';
import pc from 'picocolors';

const parser = new Parser();

function printHelp() {
  console.log(`
${pc.bold(pc.cyan('Google News CLI'))} - Get the latest news from Google News directly in your terminal.

${pc.bold('Usage:')}
  google-news [options]

${pc.bold('Options:')}
  ${pc.yellow('-s, --search <query>')}   Search for specific topics or keywords
  ${pc.yellow('-l, --limit <number>')}    Limit the number of headlines displayed (default: 10)
  ${pc.yellow('-c, --country <codecode>')} Set country/region code (default: US, e.g., IN, GB, CA)
  ${pc.yellow('--lang <language>')}       Set language code (default: en, e.g., hi, fr, es)
  ${pc.yellow('-h, --help')}              Show this help message

${pc.bold('Examples:')}
  ${pc.gray('# Get top stories')}
  node index.js
  
  ${pc.gray('# Search for tech news')}
  node index.js --search "machine learning" --limit 5
  
  ${pc.gray('# Get news in French from France')}
  node index.js --country FR --lang fr
`);
}

async function main() {
  const argv = minimist(process.argv.slice(2), {
    string: ['search', 'country', 'lang'],
    number: ['limit'],
    boolean: ['help'],
    alias: {
      s: 'search',
      l: 'limit',
      c: 'country',
      h: 'help'
    }
  });

  if (argv.help) {
    printHelp();
    return;
  }

  const limit = argv.limit || 10;
  const country = (argv.country || 'US').toUpperCase();
  const lang = (argv.lang || 'en').toLowerCase();
  const searchQuery = argv.search;

  // Build Google News RSS URL
  // Top Headlines: https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en
  // Search: https://news.google.com/rss/search?q=query&hl=en-US&gl=US&ceid=US:en
  const hl = `${lang}-${country}`;
  const ceid = `${country}:${lang}`;
  
  let url = '';
  if (searchQuery) {
    url = `https://news.google.com/rss/search?q=${encodeURIComponent(searchQuery)}&hl=${hl}&gl=${country}&ceid=${ceid}`;
  } else {
    url = `https://news.google.com/rss?hl=${hl}&gl=${country}&ceid=${ceid}`;
  }

  console.log(pc.blue(`\nFetching news from Google News...`));
  if (searchQuery) {
    console.log(pc.gray(`Search Query: "${searchQuery}" | Country: ${country} | Lang: ${lang}\n`));
  } else {
    console.log(pc.gray(`Top Headlines | Country: ${country} | Lang: ${lang}\n`));
  }

  try {
    const feed = await parser.parseURL(url);
    
    if (!feed.items || feed.items.length === 0) {
      console.log(pc.yellow('No news items found.'));
      return;
    }

    const itemsToShow = feed.items.slice(0, limit);

    itemsToShow.forEach((item, index) => {
      const title = item.title || 'No Title';
      
      // Google News titles are usually in the format: "Headline - Publisher"
      // We can extract the publisher if needed
      const dashIndex = title.lastIndexOf(' - ');
      let headline = title;
      let source = 'Unknown Source';
      
      if (dashIndex !== -1) {
        headline = title.substring(0, dashIndex).trim();
        source = title.substring(dashIndex + 3).trim();
      }

      const dateStr = item.pubDate ? new Date(item.pubDate).toLocaleString() : 'Unknown Date';

      console.log(`${pc.green(pc.bold(`${index + 1}.`))} ${pc.bold(headline)}`);
      console.log(`   ${pc.dim('Source:')} ${pc.magenta(source)} | ${pc.dim('Published:')} ${pc.gray(dateStr)}`);
      console.log(`   ${pc.dim('Link:')} ${pc.blue(pc.underline(item.link))}`);
      console.log();
    });

    console.log(pc.cyan(`Showed ${itemsToShow.length} of ${feed.items.length} articles.`));
  } catch (error) {
    console.error(pc.red(`\nError fetching news: ${error.message}`));
    console.error(pc.gray(`Ensure you are connected to the internet and that the country/language options are valid.`));
    process.exit(1);
  }
}

main();
