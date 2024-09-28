#!/usr/bin/env python3

import typer
import requests
import subprocess
import pyperclip
from plyer import notification
from pathlib import Path
from rich.console import Console

app = typer.Typer()
console = Console()


def notifier(title: str, message: str):
    notification.notify(
        app_name="ezhost",
        title=title,
        message=message,
        app_icon="https://assets.e-z.gg/e-ztransparent.png",
        ticker="ezhost",
        timeout=5,
    )


BASE_URL = "https://api.e-z.host/files"
GRIMBLAST_PATH = "/usr/bin/grimblast"


def capture_screenshot(output_file: Path, mode: str):
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

    result = subprocess.run(command, capture_output=True)
    print("Success")
    if result.returncode != 0:
        console.print(
            f"[bold red]Failed to capture screenshot: {
                result.stderr.decode()}[/bold red]",
            style="red",
        )
        raise typer.Exit(code=1)

    if not output_file.is_file():
        console.print(f"[bold red]Error: The file '{
                      output_file}' was not created.[/bold red]")
        raise typer.Exit(code=1)


def upload_screenshot(api_key: str, file_path: Path, verbose: bool):
    if not file_path.is_file():
        console.print(
            f"[bold red]Error:[/bold red] \
            The file'{file_path}' does not exist.",
            style="red",
        )
        raise typer.Exit(code=1)

    headers = {"key": api_key}

    try:
        with open(file_path, "rb") as f:
            files = {"file": f}
            response = requests.post(BASE_URL, headers=headers, files=files)

        if response.status_code == 200:
            data = response.json()
            if verbose:
                console.print("[green]File uploaded successfully![/green]")
                console.print(f"File URL: [bold cyan]{
                              data.get('imageUrl', 'N/A')}[/bold cyan]")
                console.print(f"Raw URL: [bold cyan]{
                              data.get('rawUrl', 'N/A')}[/bold cyan]")
                console.print(f"Delete URL: [bold red]{
                              data.get('deletionUrl', 'N/A')}[/bold red]")
            pyperclip.copy(image_url := data.get("rawUrl", ""))
            console.print("[green]File URL copied to clipboard![/green]")
            filename = image_url.split("/")[-1]
            notifier("e-z.gg", f"Successfully uploaded {filename}")

        else:
            console.print(
                f"[bold red]Error {
                    response.status_code}:[/bold red] {response.text}",
                style="red",
            )
    except requests.exceptions.RequestException as e:
        console.print(f"[bold red]Error:[/bold red] {e}", style="red")
        raise typer.Exit(code=1)

    file_path.unlink()


@app.command()
def partial(
    api_key: str = typer.Argument(..., help="Your API key"),
    file_name: str = typer.Option(
        "partial_capture.png", help="Name of the file to save the screenshot"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Show detailed output"),
):
    output_file = Path(file_name)
    capture_screenshot(output_file, "partial")
    upload_screenshot(api_key, output_file, verbose)


@app.command()
def fullscreen(
    api_key: str = typer.Argument(..., help="Your API key"),
    file_name: str = typer.Option(
        "fullscreen_capture.png", help="Name of the file to save the screenshot"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Show detailed output"),
):
    output_file = Path(file_name)
    capture_screenshot(output_file, "fullscreen")
    upload_screenshot(api_key, output_file, verbose)


@app.command()
def window(
    api_key: str = typer.Argument(..., help="Your API key"),
    file_name: str = typer.Option(
        "window_capture.png", help="Name of the file to save the screenshot"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Show detailed output"),
):
    output_file = Path(file_name)
    capture_screenshot(output_file, "window")
    upload_screenshot(api_key, output_file, verbose)


if __name__ == "__main__":
    app()
