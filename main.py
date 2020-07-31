import praw, os, requests, re, html.parser, time

class BlogParser(html.parser.HTMLParser):
    def __init__(self):
        html.parser.HTMLParser.__init__(self)
        self.body_depth = 0
        self.body = ''

    def handle_starttag(self, tag, attrs):
        if tag != 'div':
            return

        if self.body_depth:
            self.body_depth += 1
        else:
            for name, value in attrs:
                if name == 'class' and value == 'article__content':
                    self.body_depth += 1

    def handle_endtag(self, tag):
        if tag == 'div' and self.body_depth:
            self.body_depth -= 1

    def handle_data(self, data):
        if self.body_depth:
            self.body += data


def format_blog(url):
    blog_text = requests.get(url).content.decode()
    parser = BlogParser()
    parser.feed(blog_text)
    return parser.body
    
if __name__ == '__main__':
    reddit = praw.Reddit('wgbot', user_agent = 'wgposterbot')

    subreddit = reddit.subreddit('WorldofWarships')
    for submission in subreddit.stream.submissions():
        if submission.author.name == 'DevBlogWoWs':
            try:
                blog_url = re.search('(https\:\/\/blog.worldofwarships.com\/blog\/[\d]+)', submission.selftext)[0]
                submission.reply(format_blog(blog_url))
            except praw.exceptions.RedditAPIException as e:
                for ex in e.items:
                    if e.error_type == 'RATELIMIT':
                        wait = re.search('try again in (\d+) (minutes|seconds)', ex.message)
                        if wait[2] == 'seconds':
                            time.sleep(int(wait[1]) + 10)
                        else:
                            time.sleep(int(wait[1]) * 60 + 10)
                        submission.reply(format_blog(blog_url))
                        