import asyncio
import hmac
import hashlib
import random
from urllib.parse import unquote, quote
from time import time
import pytz
from datetime import datetime, timezone

import aiohttp
from aiocfscrape import CloudflareScraper
from pyrogram import Client
from pyrogram.errors import Unauthorized, UserDeactivated, AuthKeyUnregistered, FloodWait
from pyrogram.raw.functions.messages import RequestWebView
from bot.config import settings

from bot.utils import logger

from bot.exceptions import InvalidSession
from .headers import headers

class Tapper:
    def __init__(self, tg_client: Client):
        self.session_name = tg_client.name
        self.tg_client = tg_client
        self.user_id = 0
        self.username = None

    async def get_secret(self, userid):
        key_hash = str("adwawdasfajfklasjglrejnoierjboivrevioreboidwa").encode('utf-8')
        message = str(userid).encode('utf-8')
        hmac_obj = hmac.new(key_hash, message, hashlib.sha256)
        secret = str(hmac_obj.hexdigest())
        return secret

    async def get_tg_web_data(self) -> str:
        try:
            with_tg = True

            if not self.tg_client.is_connected:
                with_tg = False
                try:
                    await self.tg_client.connect()
                except (Unauthorized, UserDeactivated, AuthKeyUnregistered):
                    raise InvalidSession(self.session_name)

            while True:
                try:
                    peer = await self.tg_client.resolve_peer('cutlet_tap_bot')
                    break
                except FloodWait as fl:
                    fls = fl.value

                    logger.warning(f"{self.session_name} | FloodWait {fl}")
                    logger.info(f"{self.session_name} | Sleep {fls}s")

                    await asyncio.sleep(fls + 3)

            web_view = await self.tg_client.invoke(RequestWebView(
                peer=peer,
                bot=peer,
                platform='android',
                from_bot_menu=False,
                url='https://app.cutlet.fun/'
            ))

            auth_url = web_view.url

            tg_web_data = unquote(
                string=unquote(string=auth_url.split('tgWebAppData=', maxsplit=1)[1].split('&tgWebAppVersion', maxsplit=1)[0]))

            self.user_id = (await self.tg_client.get_me()).id

            if with_tg is False:
                await self.tg_client.disconnect()

            return tg_web_data

        except InvalidSession as error:
            raise error

        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error during Authorization: {error}")
            await asyncio.sleep(delay=30)


    async def auth(self, http_client: aiohttp.ClientSession):
        try:
            url = 'https://api.cutlet.fun/v1/user'
            response = await http_client.get(url=url)
            response.raise_for_status()

            response_json = await response.json()
            return response_json

        except Exception as error:
            logger.error(f"{self.session_name} | Auth Error: {error}")
            await asyncio.sleep(delay=30)
            return False

    async def passive(self, http_client: aiohttp.ClientSession, passive_action, access_token):
        try:
            match passive_action:
                case 'balance':
                    passive_url = f"https://api-bot.backend-boom.com/api/v1/balance?access_token={access_token}"
                case 'status':
                    passive_url = f"https://api-bot.backend-boom.com/api/v1/passive?access_token={access_token}"
                case 'start':
                    passive_url = f"https://api-bot.backend-boom.com/api/v1/passive/start?access_token={access_token}"
                case 'collect':
                    passive_url = f"https://api-bot.backend-boom.com/api/v1/passive/collect?access_token={access_token}"
                case _:
                    raise ValueError("There is no passive_action.")

            http_client.headers["content-type"] = "application/json"

            response = await http_client.get(url=passive_url)
            response.raise_for_status()

            response_json = await response.json()
            return response_json

        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error when Passive: {error}")
            await asyncio.sleep(delay=30)
            return False

    async def game(self, http_client: aiohttp.ClientSession, game_action: str = '', game_value: int = 0):
        try:
            match game_action:
                case 'points':
                    url = "https://api.cutlet.fun/v1/game/points"
                    logger.info(f"{self.session_name} | game | action [{game_action}]")
                    response = await http_client.get(url=url)

                case 'click':
                    url = "https://api.cutlet.fun/v1/game/click"
                    json_data = {'tapsCount': game_value}
                    print(json_data)
                    logger.info(f"{self.session_name} | game | action [{game_action}]")
                    response = await http_client.post(url=url, json=json_data)

                case _:
                    raise ValueError("There is no passive_action.")

            response.raise_for_status()

            response_json = await response.json()
            return response_json

        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error when API: {error}")
            await asyncio.sleep(delay=30)
            return False

    async def tasks(self, http_client: aiohttp.ClientSession, tasks_action: str = '', tasks_name: str = ''):
        try:
            match tasks_action:
                case 'get':
                    tasks_url = "https://api.cutlet.fun/v1/tasks"
                    response = await http_client.post(url=tasks_url)
                    response.raise_for_status()
                    response_json = await response.json()
                    return response_json

                case 'check':
                    tasks_data = {'taskId': tasks_name}
                    tasks_url = "https://api.cutlet.fun/v1/task/check"
                    response = await http_client.post(url=tasks_url, json=tasks_data)
                    response.raise_for_status()
                    if response.ok :
                        return True
                    else:
                        return False

                case 'claim':
                    tasks_data = {'taskId': tasks_name}
                    tasks_url = "https://api.cutlet.fun/v1/task/claim"
                    response = await http_client.post(url=tasks_url, json=tasks_data)
                    response.raise_for_status()
                    if response.ok :
                        return True
                    else:
                        return False

                case _:
                    raise ValueError("There is no passive_action.")


        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error when TASKS: {error}")
            await asyncio.sleep(delay=30)
            return False

    async def run(self) -> None:
        tasks_data = []

        while True:
            try:
                random_sleep = random.randint(*settings.RANDOM_SLEEP)
                waiting_sleep = random.randint(*settings.WAITING_SLEEP)

                http_client = CloudflareScraper(headers=headers)
                tg_web_data = await self.get_tg_web_data()
                http_client.headers["auth"] = f"{tg_web_data}"

                auth_data = await self.auth(http_client=http_client)
                if auth_data:
                    logger.success(f"{self.session_name} | <red>Auth</red> | "
                                   f"User: <g>{auth_data['user']['nickname']}</g>, "
                                   f"Game: tapsBalance <g>{auth_data['game']['tapsBalance']}</g>, "
                                   f"pointsBalance <g>{auth_data['game']['pointsBalance']}</g>, "
                                   f"burgerCapacity: <g>{auth_data['burgerCapacity']}</g> ")

                game_action = 'points'
                logger.info(f"{self.session_name} | sleep {random_sleep:,}s before: <g>[game/{game_action}]</g>")
                game_data = await self.game(http_client=http_client, game_action=game_action)
                if game_data:
                    logger.info(f"{self.session_name} | action: <red>[game/{game_action}]</red> : <c>{game_data}</c>")
                    points = game_data['points']
                    limitPoints = game_data['limitPoints']

                if settings.AUTO_TASK:
                    # get tasks
                    tasks_action = 'get'
                    logger.info(f"{self.session_name} | sleep {random_sleep:,}s before [tasks/{tasks_action}]")
                    await asyncio.sleep(delay=random_sleep)
                    tasks_data = await self.tasks(http_client=http_client, tasks_action=tasks_action)
                    if tasks_data:
                        logger.success(f"{self.session_name} | action: <red>[tasks/{tasks_action}]</red> : <c>{tasks_data}</c>")
                    else:
                        logger.info(f"{self.session_name} | Cannot action: <c>[tasks/{tasks_action}]</c>")

                    tasks = [{'id': task['id'], 'status': task['status']} for task in tasks_data['tasks'].values() if task["status"] != "completed"]
                    print(tasks)

                    for task in tasks:
                        match task['status']:
                            case 'new':
                                print(task['id'], task['status'])
                                task_action = 'check'
                                logger.info(f"{self.session_name} | sleep {random_sleep:,}s before: "
                                            f"<g>[task/{task_action}]:</g> <c>{task['id']}</c>")
                                await asyncio.sleep(delay=random_sleep)
                                task_data = await self.tasks(http_client=http_client,
                                                             tasks_action=task_action, tasks_name=task['id'])
                                if task_data:
                                    logger.success(f"{self.session_name} | action: <red>[task/{task_action}/{task['id']}]</red> : <c>{task_data}</c>")

                            case 'canClaim':
                                print(task['id'], task['status'])
                                task_action = 'claim'
                                logger.info(f"{self.session_name} | sleep {random_sleep:,}s before: "
                                            f"<g>[task/{task_action}]:</g> <c>{task['id']}</c>")
                                await asyncio.sleep(delay=random_sleep)
                                task_data = await self.tasks(http_client=http_client,
                                                             tasks_action=task_action, tasks_name=task['id'])
                                if task_data:
                                    logger.success(f"{self.session_name} | action: <red>[task/{task_action}/{task['id']}]</red> : <c>{task_data}</c>")

                if settings.AUTO_TAP and points != limitPoints:
                    game_action = 'click'
                    game_value = limitPoints - points
                    logger.info(f"{self.session_name} | sleep {random_sleep:,}s before: <g>[game/{game_action}]</g>")
                    game_data = await self.game(http_client=http_client, game_action=game_action, game_value=game_value)
                    if game_data:
                        logger.info(f"{self.session_name} | action: <red>[game/{game_action}/{game_value}]</red> : <c>{game_data}</c>")

                #Final SLEEP
                logger.info(f"{self.session_name} | Waiting sleep {waiting_sleep:,}s")
                await http_client.close()
                await asyncio.sleep(delay=waiting_sleep)

            except InvalidSession as error:
                raise error

            except Exception as error:
                logger.error(f"{self.session_name} | Unknown error: {error}")
                await http_client.close()
                await asyncio.sleep(delay=30)


async def run_tapper(tg_client: Client):
    try:
        await Tapper(tg_client=tg_client).run()
    except InvalidSession:
        logger.error(f"{tg_client.name} | Invalid Session")
