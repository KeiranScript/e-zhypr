#!/usr/bin/env python3

import typer
import pyperclip
import configparser
from PIL import Image
import io
from pathlib import Path
from rich.console import Console
from rich.prompt import Prompt
from plyer import notification
import datetime
import aiofiles
import aiohttp
import asyncio
import logging
from rich.progress import Progress

config = configparser.ConfigParser()
config_file = Path.home() / ".config" / "e-zhypr" / "config.ini"
history_file = Path.home() / ".cache" / "e-zhypr" / "files"

if not config_file.exists():
    config["DEFAULT"] = {
        "BASE_URL": "https://api.e-z.host/files",
        "GRIMBLAST_PATH": "/usr/bin/grimblast",
        "API_KEY": "",
        "COMPRESSION_LEVEL": "0",
        "SAVE_TO_DISK": "True",
        "SAVE_DIRECTORY": str(Path.home() / "Screenshots"),
        "DEFAULT_SERVICE": "ezhost",
        "IMAGE_FORMAT": "png",
        "VERBOSE": "False",
        "RAW_FILE": "False",
        "ANNOTATION_FONT": "fonts/Inter-Regular.ttf",
        "ANNOTATION_COLOR": "white",
    }
    config_file.parent.mkdir(parents=True, exist_ok=True)
    with config_file.open("w") as f:
        config.write(f)

config.read(config_file)

BASE_URL = config.get("DEFAULT", "BASE_URL", fallback="https://api.e-z.host/files")
GRIMBLAST_PATH = config.get("DEFAULT", "GRIMBLAST_PATH", fallback="/usr/bin/grimblast")
API_KEY = config.get("DEFAULT", "API_KEY", fallback="")
COMPRESSION_LEVEL = config.getint("DEFAULT", "COMPRESSION_LEVEL", fallback=0)
SAVE_TO_DISK = config.getboolean("DEFAULT", "SAVE_TO_DISK", fallback=True)
SAVE_DIRECTORY = Path(
    config.get("DEFAULT", "SAVE_DIRECTORY", fallback=str(Path.home() / "Screenshots"))
)
DEFAULT_SERVICE = config.get("DEFAULT", "DEFAULT_SERVICE", fallback="ezhost")
IMAGE_FORMAT = config.get("DEFAULT", "IMAGE_FORMAT", fallback="png")
VERBOSE = config.getboolean("DEFAULT", "VERBOSE", fallback=False)
RAW_FILE = config.getboolean("DEFAULT", "RAW_FILE", fallback=False)
ANNOTATION_FONT = config.get(
    "DEFAULT", "ANNOTATION_FONT", fallback="fonts/Inter-Regular.ttf"
)
ANNOTATION_COLOR = config.get("DEFAULT", "ANNOTATION_COLOR", fallback="white")

app = typer.Typer(
    add_completion=False,
    no_args_is_help=True,
    rich_help_panel="e-z.host",
    help="Capture screenshots and upload them to e-z.host (or other services)",
    pretty_exceptions_enable=True,
    pretty_exceptions_show_locals=True,
    pretty_exceptions_short=True,
)
console = Console(soft_wrap=True)

# Logging setup
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
file_handler = logging.FileHandler("e-zhypr.log")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


def notifier(title: str, message: str):
    notification.notify(
        app_name="ezhost",
        title=title,
        message=message,
        app_icon="https://assets.e-z.gg/e-ztransparent.png",
        ticker="ezhost",
        timeout=5,
    )


def generate_filename():
    now = datetime.datetime.now()
    filename = f"screenshot_{now.strftime('%H:%M')}.{IMAGE_FORMAT}"
    if (SAVE_DIRECTORY / filename).exists():
        filename = f"screenshot_{now.strftime('%H:%M:%S')}.{IMAGE_FORMAT}"
    return filename


async def capture_screenshot(output_file: Path, mode: str):
    command = []
    if mode == "partial":
        command = [GRIMBLAST_PATH, "save", "area", str(output_file)]
    elif mode == "fullscreen":
        command = [GRIMBLAST_PATH, "save", "screen", str(output_file)]
    elif mode == "window":
        command = [GRIMBLAST_PATH, "save", "active", str(output_file)]
    else:
        console.print("[bold red]Invalid capture mode[/bold red]", style="red")
        raise typer.Exit(code=1)

    output_file.parent.mkdir(parents=True, exist_ok=True)

    process = await asyncio.create_subprocess_exec(
        *command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()

    with Progress() as progress:
        task = progress.add_task("[green]Capturing screenshot...", total=100)
        for i in range(100):
            await asyncio.sleep(0.005)
            progress.update(task, advance=1)

    if VERBOSE:
        console.print("[bold green]Screenshot captured successfully[/bold green]")
        logger.info("Screenshot captured successfully")
    if process.returncode != 0:
        console.print(
            f"[bold red]Failed to capture screenshot: {
                stderr.decode()}[/bold red]",
            style="red",
        )
        logger.error(f"Failed to capture screenshot: {stderr.decode()}")
        raise typer.Exit(code=1)

    if not output_file.is_file():
        console.print(f"[bold red]Error: The file '{
                      output_file}' was not created.[/bold red]")
        logger.error(f"Error: The file '{output_file}' was not created.")
        raise typer.Exit(code=1)

    return output_file


async def upload_screenshot(api_key: str, file_path: Path, verbose: bool):
    if not file_path.is_file():
        console.print(
            f"[bold red]Error:[/bold red] The file '{
                file_path}' does not exist.",
            style="red",
        )
        logger.error(f"Error: The file '{file_path}' does not exist.")
        raise typer.Exit(code=1)

    headers = {"key": api_key}

    async with aiohttp.ClientSession() as session:
        try:
            async with aiofiles.open(file_path, "rb") as f:
                files = {"file": await f.read()}
                async with session.post(
                    BASE_URL, headers=headers, data=files
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        if verbose:
                            console.print(
                                "[bold green]File uploaded successfully![/bold green]"
                            )
                            logger.info("File uploaded successfully")
                            console.print(f"File URL: [bold cyan]{
                                          data.get('imageUrl', 'N/A')}[/bold cyan]")
                            logger.info(f"File URL: {data.get('imageUrl', 'N/A')}")
                            console.print(f"Raw URL: [bold cyan]{
                                          data.get('rawUrl', 'N/A')}[/bold cyan]")
                            logger.info(f"Raw URL: {data.get('rawUrl', 'N/A')}")
                            console.print(f"Delete URL: [bold red]{
                                          data.get('deletionUrl', 'N/A')}[/bold red]")
                            logger.info(f"Delete URL: {
                                        data.get('deletionUrl', 'N/A')}")
                        file_url = (
                            data.get("rawUrl", "")
                            if RAW_FILE
                            else data.get("imageUrl", "")
                        )
                        pyperclip.copy(file_url)
                        console.print(
                            "[bold green]File URL copied to clipboard![/bold green]"
                        )
                        logger.info("File URL copied to clipboard")
                        filename = file_url.split("/")[-1]
                        notifier("e-z.gg", f"Successfully uploaded {filename}")

                        history_file.parent.mkdir(parents=True, exist_ok=True)
                        with history_file.open("a") as hf:
                            hf.write(f"{file_url}\n")
                    else:
                        console.print(
                            f"[bold red]Error {response.status}:[/bold red] {await response.text()}",
                            style="red",
                        )
                        logger.error(
                            f"Error {response.status}: {await response.text()}"
                        )
        except aiohttp.ClientError as e:
            console.print(f"[bold red]Error:[/bold red] {e}", style="red")
            logger.error(f"Error: {e}")
            raise typer.Exit(code=1)
        finally:
            if not SAVE_TO_DISK and file_path.exists():
                file_path.unlink()


def compress_image(file_path: Path, quality: int = COMPRESSION_LEVEL):
    with Image.open(file_path) as img:
        buffer = io.BytesIO()
        if quality == 0:
            img.save(buffer, format=IMAGE_FORMAT.upper(), optimize=True)
        else:
            img.save(
                buffer, format=IMAGE_FORMAT.upper(), optimize=True, quality=quality
            )
        buffer.seek(0)
    return buffer


def get_api_key():
    global API_KEY
    if not API_KEY:
        API_KEY = Prompt.ask("[bold cyan]Please enter your API key[/bold cyan]")
        config["DEFAULT"]["API_KEY"] = API_KEY
        with config_file.open("w") as f:
            config.write(f)
    return API_KEY


@app.command(help="Capture a partial screenshot and upload it.")
def partial(
    file_name: str = typer.Option(
        None, help="Specify the name of the file to save the screenshot."
    ),
    verbose: bool = typer.Option(
        VERBOSE, "--verbose", "-v", help="Enable detailed output."
    ),
    service: str = typer.Option(
        DEFAULT_SERVICE,
        "--service",
        "-s",
        help="Choose the upload service to use (e.g., ezhost, anonhost, ferrethost).",
    ),
):
    api_key = get_api_key()
    if file_name is None:
        file_name = generate_filename()
    output_file = SAVE_DIRECTORY / file_name if SAVE_TO_DISK else Path(file_name)
    asyncio.run(capture_screenshot(output_file, "partial"))
    if service == "ezhost":
        asyncio.run(upload_screenshot(api_key, output_file, verbose))
    else:
        console.print(f"[bold red]Unsupported upload service: {
                      service}[/bold red]")


@app.command(help="Capture a fullscreen screenshot and upload it.")
def fullscreen(
    file_name: str = typer.Option(
        None, help="Specify the name of the file to save the screenshot."
    ),
    verbose: bool = typer.Option(
        VERBOSE, "--verbose", "-v", help="Enable detailed output."
    ),
):
    api_key = get_api_key()
    if file_name is None:
        file_name = generate_filename()
    output_file = SAVE_DIRECTORY / file_name if SAVE_TO_DISK else Path(file_name)
    asyncio.run(capture_screenshot(output_file, "fullscreen"))
    asyncio.run(upload_screenshot(api_key, output_file, verbose))


@app.command(help="Capture a window screenshot and upload it.")
def window(
    file_name: str = typer.Option(
        None, help="Specify the name of the file to save the screenshot."
    ),
    verbose: bool = typer.Option(
        VERBOSE, "--verbose", "-v", help="Enable detailed output."
    ),
):
    api_key = get_api_key()
    if file_name is None:
        file_name = generate_filename()
    output_file = SAVE_DIRECTORY / file_name if SAVE_TO_DISK else Path(file_name)
    asyncio.run(capture_screenshot(output_file, "window"))
    asyncio.run(upload_screenshot(api_key, output_file, verbose))


@app.command(help="Upload an image from the clipboard.")
def clipboard(
    verbose: bool = typer.Option(
        VERBOSE, "--verbose", "-v", help="Enable detailed output."
    ),
):
    import time
    from PIL import ImageGrab

    time.sleep(0.5)
    img = ImageGrab.grabclipboard()
    if img:
        buffer = io.BytesIO()
        img.save(buffer, format=IMAGE_FORMAT.upper())
        buffer.seek(0)
        asyncio.run(upload_screenshot(get_api_key(), buffer, verbose))
    else:
        console.print("[bold red]No image found in clipboard.[/bold red]")
        logger.error("No image found in clipboard.")
        raise typer.Exit(code=1)


@app.command(help="Show upload history.")
def history():
    if history_file.exists():
        with history_file.open("r") as hf:
            history_content = hf.read().strip()
            if history_content:
                console.print("[bold green]Upload History:[/bold green]")
                console.print(history_content)
            else:
                console.print("[bold yellow]No upload history found.[/bold yellow]")
    else:
        console.print("[bold yellow]No upload history found.[/bold yellow]")


@app.command(help="Clear upload history.")
def clear_history():
    if history_file.exists():
        history_file.unlink()
        console.print("[bold green]Upload history cleared.[/bold green]")
    else:
        console.print("[bold yellow]No upload history to clear.[/bold yellow]")


if __name__ == "__main__":
    app()

