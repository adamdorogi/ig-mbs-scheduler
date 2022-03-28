import os
import pyperclip
import subprocess
from dateutil import parser
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from ig_mbs_scheduler.drivers.base_driver import BaseWebDriver
from ig_mbs_scheduler.drivers.mbs.constants import osascripts, xpaths


class MBSWebDriver(BaseWebDriver):
    """
    A `selenium` web driver class for performing Meta Business Suite (MBS) web operations.

    Parameters
    ----------
    session_id : str
        An arbitrary identifier for the MBS session (for example, a Facebook email address).
    asset_id : str
        The MBS asset ID for which to schedule posts.
    prefer_video : bool, default=False
        MBS only allows either photos or videos in a carousel post. When scheduling a carousel, this flag will prefer videos over photos.
    upload_timeout : int, default=60
        The maximum duration to wait when uploading media to MBS.
    timeout : int, default=5
        The maximum duration to wait for elements to load.

    Attributes
    ----------
    asset_id : str
        The MBS asset ID for which to schedule posts.
    prefer_video : bool
        MBS only allows either photos or videos in a carousel post. When scheduling a carousel, this flag will prefer videos over photos.
    upload_timeout : int
        The maximum duration to wait when uploading media to MBS.
    """

    def __init__(
        self,
        session_id,
        asset_id,
        prefer_video=False,
        upload_timeout=60,
        timeout=5,
    ):
        super().__init__(f"mbs/{session_id}", timeout)
        self.asset_id = asset_id
        self.prefer_video = prefer_video
        self.upload_timeout = upload_timeout

    def schedule_post(self, datetime, media_dir_path, caption):
        """
        Schedule a post.

        Parameters
        ----------
        datetime : datetime
            The `datetime` for which to schedule the post.
        media_dir_path : str
            The path of the folder containing the media to schedule.
        caption : str
            The caption to add to the scheduled post.
        """
        self._get(f"https://business.facebook.com/latest/home?asset_id={self.asset_id}")

        post_schedule_button = WebDriverWait(self._driver, self.timeout).until(
            EC.element_to_be_clickable((By.XPATH, xpaths.PLANNER_SCHEDULE_POST_DIV))
        )
        post_schedule_button.click()

        self.__pick_date(datetime)

        # Select post placement
        self.__select_placement(False, True)

        # Enter post caption
        schedule_caption_div = self._driver.find_element(
            By.XPATH, xpaths.SCHEDULE_CAPTION_DIV
        )
        clipboard = pyperclip.paste()  # Save clipboard
        pyperclip.copy(caption)
        schedule_caption_div.send_keys(Keys.COMMAND + "v")
        pyperclip.copy(clipboard)  # Restore saved clipboard

        # Check whether saved media has photos or videos
        is_file_video = {
            os.path.splitext(filename)[1] == ".mp4"
            for filename in os.listdir(media_dir_path)
        }
        has_photos = False in is_file_video
        has_videos = True in is_file_video

        # Choose files
        schedule_add_photo_link = self._driver.find_element(
            By.XPATH,
            xpaths.SCHEDULE_ADD_VIDEO_LINK
            if not has_photos or (has_videos and self.prefer_video)
            else xpaths.SCHEDULE_ADD_PHOTO_LINK,
        )
        schedule_add_photo_link.click()
        self.__choose_files(media_dir_path)

        # Click schedule button
        self.__publish_schedule()

        print("Successfully scheduled post")

    def schedule_story(self, datetime, media_dir_path):
        """
        Schedule a story.

        Parameters
        ----------
        datetime : datetime
            The `datetime` for which to schedule the story.
        media_dir_path : str
            The path of the folder containing the media to schedule.
        """
        self._get(f"https://business.facebook.com/latest/home?asset_id={self.asset_id}")

        planner_dropdown_div = WebDriverWait(self._driver, self.timeout).until(
            EC.element_to_be_clickable((By.XPATH, xpaths.PLANNER_DROPDOWN_DIV))
        )
        planner_dropdown_div.click()

        planner_schedule_story_div = self._driver.find_element(
            By.XPATH, xpaths.PLANNER_SCHEDULE_STORY_DIV
        )
        planner_schedule_story_div.click()

        self.__pick_date(datetime)

        # Select post placement
        self.__select_placement(False, True)

        # Choose files
        schedule_add_media_div = self._driver.find_element(
            By.XPATH, xpaths.SCHEDULE_ADD_MEDIA_DIV
        )
        schedule_add_media_div.click()
        self.__choose_files(media_dir_path)

        # Click schedule button
        self.__publish_schedule()

        print("Successfully scheduled story")

    def get_scheduled_post_dates(self):
        """
        Get the dates of scheduled posts.

        Returns
        -------
        list of datetime
            The dates of scheduled posts.
        """
        self._get(
            f"https://business.facebook.com/latest/posts/scheduled_posts?asset_id={self.asset_id}"
        )

        try:
            scheduled_post_date_spans = WebDriverWait(self._driver, self.timeout).until(
                EC.presence_of_all_elements_located(
                    (By.XPATH, xpaths.SCHEDULED_POST_DATE_SPANS)
                )
            )
        except TimeoutException:
            print("No posts scheduled")
            return []

        scheduled_post_dates = [
            parser.parse(scheduled_post_date_span.text)
            for scheduled_post_date_span in scheduled_post_date_spans
            if scheduled_post_date_span.text != ""
        ]

        print(f"Successfully got scheduled post dates: {scheduled_post_dates}")

        return scheduled_post_dates

    def get_scheduled_story_dates(self):
        """
        Get the dates of scheduled stories.

        Returns
        -------
        list of datetime
            The dates of scheduled stories.
        """
        self._get(
            f"https://business.facebook.com/latest/posts/scheduled_stories?asset_id={self.asset_id}"
        )

        try:
            scheduled_post_story_spans = WebDriverWait(
                self._driver, self.timeout
            ).until(
                EC.presence_of_all_elements_located(
                    (By.XPATH, xpaths.SCHEDULED_STORY_DATE_SPANS)
                )
            )
        except TimeoutException:
            print("No stories scheduled")
            return []

        scheduled_story_dates = [
            parser.parse(scheduled_post_date_span.text)
            for scheduled_post_date_span in scheduled_post_story_spans
        ]

        print(f"Successfully got scheduled story dates: {scheduled_story_dates}")

        return scheduled_story_dates

    def __pick_date(self, datetime):
        """ """
        schedule_date_input = WebDriverWait(self._driver, self.timeout).until(
            EC.element_to_be_clickable((By.XPATH, xpaths.SCHEDULE_DATE_INPUT))
        )
        schedule_date_input.click()
        schedule_date_input.send_keys(Keys.COMMAND + "a")
        schedule_date_input.send_keys(datetime.strftime("%d/%m/%Y"))

        schedule_hour_input = self._driver.find_element(
            By.XPATH, xpaths.SCHEDULE_HOUR_INPUT
        )
        schedule_hour_input.click()
        schedule_hour_input.send_keys(datetime.strftime("%I"))

        schedule_minute_input = self._driver.find_element(
            By.XPATH, xpaths.SCHEDULE_MINUTE_INPUT
        )
        schedule_minute_input.click()
        schedule_minute_input.send_keys(datetime.strftime("%M"))

        schedule_period_input = self._driver.find_element(
            By.XPATH, xpaths.SCHEDULE_PERIOD_INPUT
        )
        schedule_period_input.click()
        schedule_period_input.send_keys(datetime.strftime("%p"))

        schedule_save_button = self._driver.find_element(
            By.XPATH, xpaths.SCHEDULE_SAVE_BUTTON
        )
        schedule_save_button.click()

    def __choose_files(self, media_dir_path):
        """ """
        choose_files_script = osascripts.SELECT_FILES_SCRIPT

        subprocess.run(
            [
                "/usr/bin/osascript",
                "-e",
                choose_files_script,
                os.path.abspath(media_dir_path),
            ],
            check=True,
        )

    def __publish_schedule(self):
        """ """
        schedule_publish_div = WebDriverWait(self._driver, self.upload_timeout).until(
            EC.element_to_be_clickable((By.XPATH, xpaths.SCHEDULE_PUBLISH_DIV))
        )
        schedule_publish_div.click()

    def __select_placement(self, facebook, instagram):
        """ """
        (
            schedule_facebook_placement_input,
            schedule_instagram_placement_input,
        ) = self._driver.find_elements(By.XPATH, xpaths.SCHEDULE_PLACEMENT_INPUTS)

        facebook_placement_selected = (
            schedule_facebook_placement_input.get_attribute("aria-checked") == "true"
        )
        instagram_placement_selected = (
            schedule_instagram_placement_input.get_attribute("aria-checked") == "true"
        )

        if (facebook and not facebook_placement_selected) or (
            not facebook and facebook_placement_selected
        ):
            schedule_facebook_placement_input.click()

        if (instagram and not instagram_placement_selected) or (
            not instagram and instagram_placement_selected
        ):
            schedule_instagram_placement_input.click()
