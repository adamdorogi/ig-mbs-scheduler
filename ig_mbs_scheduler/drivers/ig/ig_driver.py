import json
import re
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from ig_mbs_scheduler.drivers.base_driver import BaseWebDriver
from ig_mbs_scheduler.drivers.ig.constants import xpaths


class IGWebDriver(BaseWebDriver):
    """
    A `selenium` web driver class for performing Instagram web operations.

    Parameters
    ----------
    username : str
        The Instagram username for which to run the session.
    timeout : int, default=5
        The maximum duration to wait for elements to load.

    Attributes
    ----------
    username : str
        The Instagram username for which to run the session.
    """

    def __init__(self, username, timeout=5):
        super().__init__(f"ig/{username}", timeout)
        self.username = username

    def get_saved_collection_names(self):
        """
        Get the names of all saved collections.

        Returns
        -------
        list of str
            The names of all saved collections.
        """
        self._get(f"https://www.instagram.com/{self.username}/saved/")

        try:
            collection_divs = WebDriverWait(self._driver, self.timeout).until(
                EC.presence_of_all_elements_located((By.XPATH, xpaths.COLLECTION_DIVS))
            )
        except TimeoutException:
            print("No saved collections")
            return []

        collection_names = [collection_div.text for collection_div in collection_divs]

        print(f"Successfully got collection names: {collection_names}")

        return collection_names

    def __get_collection_div(self, collection_name):
        self._get(f"https://www.instagram.com/{self.username}/saved/")

        collection_div = WebDriverWait(self._driver, self.timeout).until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    xpaths.COLLECTION_DIV.format(collection_name=collection_name),
                )
            )
        )
        return collection_div

    def __open_collection(self, collection_name):
        collection_div = self.__get_collection_div(collection_name)
        collection_div.click()

    def __is_collection_empty(self, collection_name):
        collection_div = self.__get_collection_div(collection_name)

        collection_div_grandchildren = collection_div.find_elements(
            By.XPATH, "./div/div"
        )

        return len(collection_div_grandchildren) == 1

    def delete_collection(self, collection_name):
        """
        Delete a saved collection.

        Parameters
        ----------
        collection_name : str
            The name of the collection to delete.
        """
        self.__open_collection(collection_name)

        collection_options_button = WebDriverWait(self._driver, self.timeout).until(
            EC.presence_of_element_located((By.XPATH, xpaths.COLLECTION_OPTIONS_BUTTON))
        )
        collection_options_button.click()

        collection_delete_button = self._driver.find_element(
            By.XPATH, xpaths.COLLECTION_DELETE_BUTTON
        )
        collection_delete_button.click()

        collection_delete_confirm_button = self._driver.find_element(
            By.XPATH, xpaths.COLLECTION_DELETE_CONFIRM_BUTTON
        )
        collection_delete_confirm_button.click()

        print(f"Successfully deleted collection: {collection_name}")

    def get_collection_item_urls(self, collection_name):
        """
        Get the saved item URLs in a collection.

        Parameters
        ----------
        collection_name : str
            The collection name for which to get saved item URLs.

        Returns
        -------
        list of str
            The saved item URLs in the collection.
        """
        if self.__is_collection_empty(collection_name):
            print("No items in collection")
            return []
        self.__open_collection(collection_name)

        collection_item_links = WebDriverWait(self._driver, self.timeout).until(
            EC.presence_of_all_elements_located(
                (By.XPATH, xpaths.COLLECTION_ITEM_LINKS)
            )
        )

        collection_item_urls = [
            collection_item_link.get_attribute("href")
            for collection_item_link in collection_item_links
        ]

        print(f"Successfully got collection item URLs: {collection_item_urls}")

        return collection_item_urls

    def __get_post_data(self, post_url):
        self._get(post_url)

        post_data_script = self._driver.find_element(By.XPATH, "/html/body/script[12]")
        post_data_script_text = post_data_script.get_attribute("text")
        post_data_text = re.search(
            "window\.__additionalDataLoaded\(.*?,(.*)\);",
            post_data_script_text,
        ).group(1)
        post_data = json.loads(post_data_text)

        return post_data["items"][0]

    def __get_post_media_urls(self, post_data):
        media_type = post_data["media_type"]

        if media_type == 1:  # Photo
            photo_url = post_data["image_versions2"]["candidates"][0]["url"]
            return [photo_url]
        elif media_type == 2:  # Video
            video_url = post_data["video_versions"][0]["url"]
            return [video_url]
        elif media_type == 8:  # Carousel
            return [
                carousel_item_url
                for carousel_item_data in post_data["carousel_media"]
                for carousel_item_url in self.__get_post_media_urls(carousel_item_data)
            ]
        else:
            print(f"Unsupported media type: {media_type}")
            return []

    def get_post_media_urls(self, post_url):
        """
        Get the media URLs of a post.

        Parameters
        ----------
        post_url : str
            The URL of the post for which to get the media URLs.

        Returns
        -------
        list of str
            The media URLs of the post.
        """
        post_data = self.__get_post_data(post_url)
        media_urls = self.__get_post_media_urls(post_data)

        print(f"Successfully got post media URLs ({post_url}): {media_urls}")

        return media_urls

    def get_post_caption(self, post_url):
        """
        Get the caption of a post.

        Parameters
        ----------
        post_url : str
            The URL of the post for which to get the caption.

        Returns
        -------
        str
            The caption of the post.
        """
        post_data = self.__get_post_data(post_url)

        if post_data["caption"]:
            post_caption = post_data["caption"]["text"]
        else:
            post_caption = None

        print(f"Successfully got post caption ({post_url}): {post_caption}")

        return post_caption

    def get_post_user(self, post_url):
        """
        Get the user of a post.

        Parameters
        ----------
        post_url : str
            The URL of the post for which to get the user.

        Returns
        -------
        str
            The user of the post.
        """
        post_data = self.__get_post_data(post_url)

        post_user = post_data["user"]["username"]

        print(f"Successfully got post user ({post_url}): {post_user}")

        return post_user

    def unsave_post(self, post_url):
        """
        Unsave a post.

        Parameters
        ----------
        post_url : str
            The URL of the post to unsave.
        """
        self._get(post_url)

        try:
            post_unsave_button = self._driver.find_element(
                By.XPATH, xpaths.POST_UNSAVE_BUTTON
            )
            post_unsave_button.click()
        except NoSuchElementException:
            print(f"Post is not saved, continuing... ({post_url})")
            return

        try:
            post_unsave_prompt_button = self._driver.find_element(
                By.XPATH, xpaths.POST_UNSAVE_PROMPT_BUTTON
            )
            post_unsave_prompt_button.click()
        except NoSuchElementException:
            print(f"Successfully unsaved post ({post_url})")
            return

        print(f"Successfully unsaved post from collection ({post_url})")

    def like_post(self, post_url):
        """
        Like a post.

        Parameters
        ----------
        post_url : str
            The URL of the post to like.
        """
        self._get(post_url)

        try:
            post_like_button = self._driver.find_element(
                By.XPATH, xpaths.POST_LIKE_BUTTON
            )
            post_like_button.click()
        except NoSuchElementException:
            print(f"Post is already liked, continuing... ({post_url})")
            return

        print(f"Successfully liked post ({post_url})")
