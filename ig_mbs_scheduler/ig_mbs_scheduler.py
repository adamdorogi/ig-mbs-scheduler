import click
import random
import tempfile
import time
from copy import deepcopy
from croniter import croniter, CroniterBadCronError
from datetime import datetime
from dateutil.relativedelta import relativedelta

from ig_mbs_scheduler import utils
from ig_mbs_scheduler.drivers.ig.ig_driver import IGWebDriver
from ig_mbs_scheduler.drivers.mbs.mbs_driver import MBSWebDriver


CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])


def __validate_cron_spec(ctx, param, value):
    try:
        return croniter(value)
    except CroniterBadCronError as e:
        raise click.BadParameter(e)


@click.command(context_settings=CONTEXT_SETTINGS)
@click.version_option(None, "-v", "--version")
@click.argument("ig-username")
@click.argument("mbs-session-id")
@click.argument("mbs-asset-id")
@click.argument("post-cron-spec", type=click.UNPROCESSED, callback=__validate_cron_spec)
@click.argument(
    "story-cron-spec", type=click.UNPROCESSED, callback=__validate_cron_spec
)
@click.option(
    "--caption-template",
    "-c",
    default="{caption}",
    show_default=True,
    help="Caption template to be used for final posts. Supports {caption}, {hashtags}, and {user} format variables.",
)
@click.option(
    "--hashtags",
    "-s",
    multiple=True,
    help="Hashtags to use for {hashtags} format variable in caption template, when not re-using original post hashtags.",
)
@click.option(
    "--ignore",
    "-i",
    multiple=True,
    default=("All posts", "All Posts"),
    show_default=True,
    help="Saved collection names to ignore.",
)
@click.option(
    "--timeout",
    "-t",
    default=5,
    show_default=True,
    help="Web driver timeout (seconds).",
)
@click.option(
    "--upload-timeout",
    "-u",
    default=60,
    show_default=True,
    help="Web driver timeout when uploading content to MBS (seconds).",
)
@click.option(
    "--prefer-video",
    "-p",
    is_flag=True,
    help="MBS only allows either photos or videos in a carousel post. When reposting a carousel, this flag will prefer videos over photos.",
)
@click.option(
    "--post-cron-variability",
    "-pv",
    show_default=True,
    type=click.IntRange(0),
    default=0,
    help="A random time offset (minutes) for the post cron specification. For example, a value of 10 would randomly add +/- 10 minutes to each iteration of the post cron specificartion.",
)
@click.option(
    "--story-cron-variability",
    "-sv",
    show_default=True,
    type=click.IntRange(0),
    default=0,
    help="A random time offset (minutes) for the story cron specification. For example, a value of 10 would randomly add +/- 10 minutes to each iteration of the story cron specificartion.",
)
@click.option(
    "--amount",
    "-a",
    type=click.IntRange(1),
    help="Number of posts to schedule. If not specified, all posts will be scheduled.",
)
def cli(
    ig_username,
    mbs_session_id,
    mbs_asset_id,
    post_cron_spec,
    story_cron_spec,
    caption_template,
    hashtags,
    ignore,
    timeout,
    upload_timeout,
    prefer_video,
    post_cron_variability,
    story_cron_variability,
    amount,
):
    """
    A tool for scraping saved posts from Instagram, and scheduling them on Meta Business Suite.
    """
    with IGWebDriver(ig_username, timeout) as ig_driver, MBSWebDriver(
        mbs_session_id,
        mbs_asset_id,
        prefer_video,
        upload_timeout,
        timeout,
    ) as mbs_driver:
        # Set up post cron schedule
        scheduled_post_dates = mbs_driver.get_scheduled_post_dates()
        latest_scheduled_post_date = (
            datetime.now()
            if len(scheduled_post_dates) == 0
            else scheduled_post_dates[-1]
        )
        next_available_post_date = max(
            datetime.now() + relativedelta(minutes=20),
            latest_scheduled_post_date,
        )
        post_cron_base_date = next_available_post_date + relativedelta(
            minutes=post_cron_variability
        )
        post_cron_spec.set_current(post_cron_base_date)

        # Set up story cron schedule
        scheduled_story_dates = mbs_driver.get_scheduled_story_dates()
        latest_scheduled_story_date = (
            datetime.now()
            if len(scheduled_story_dates) == 0
            else scheduled_story_dates[-1]
        )
        next_available_story_date = max(
            datetime.now() + relativedelta(minutes=20),
            latest_scheduled_story_date,
        )
        story_cron_base_date = next_available_story_date + relativedelta(
            minutes=story_cron_variability
        )
        story_cron_spec.set_current(story_cron_base_date)

        schedule_count = 0
        retry_count = 0
        while schedule_count < amount if amount else True:
            try:
                # Back up cron iterators, so we can restore in case of error
                post_cron_spec_backup = deepcopy(post_cron_spec)
                story_cron_spec_backup = deepcopy(story_cron_spec)

                # Get random post
                collection_names = set(
                    filter(
                        lambda collection_name: collection_name not in ignore,
                        ig_driver.get_saved_collection_names(),
                    )
                )
                if len(collection_names) == 0:
                    break
                random_collection_name = random.sample(collection_names, 1)[0]
                collection_item_urls = ig_driver.get_collection_item_urls(
                    random_collection_name
                )
                random_collection_item_url = random.sample(collection_item_urls, 1)[0]

                # Get post content
                media_urls = ig_driver.get_post_media_urls(random_collection_item_url)
                caption = ig_driver.get_post_caption(random_collection_item_url)
                user = ig_driver.get_post_user(random_collection_item_url)

                with tempfile.TemporaryDirectory() as media_dir_path:
                    utils.download_media(media_urls, media_dir_path)

                    final_caption = utils.create_final_caption(
                        random_collection_name,
                        caption,
                        user,
                        caption_template,
                        set(hashtags),
                    )

                    if final_caption is None:
                        # Schedule story
                        story_random_variance = random.randint(
                            -story_cron_variability, story_cron_variability
                        )
                        story_schedule_date = story_cron_spec.next(
                            datetime
                        ) + relativedelta(minutes=story_random_variance)
                        mbs_driver.schedule_story(story_schedule_date, media_dir_path)
                    else:
                        # Schedule post
                        post_random_variance = random.randint(
                            -post_cron_variability, post_cron_variability
                        )
                        post_schedule_date = post_cron_spec.next(
                            datetime
                        ) + relativedelta(minutes=post_random_variance)
                        mbs_driver.schedule_post(
                            post_schedule_date, media_dir_path, final_caption
                        )

                # Unsave and like post
                ig_driver.unsave_post(random_collection_item_url)
                ig_driver.like_post(random_collection_item_url)

                # Delete collection if empty
                if len(ig_driver.get_collection_item_urls(random_collection_name)) == 0:
                    ig_driver.delete_collection(random_collection_name)

                schedule_count += 1
                retry_count = 0
            except Exception as e:
                print(f"An error occured: {e}")

                delay = 2**retry_count
                print(f"Retrying in {delay} seconds...")
                time.sleep(delay)

                retry_count += 1

                # Restore cron iterator backups
                post_cron_spec = post_cron_spec_backup
                story_cron_spec = story_cron_spec_backup
