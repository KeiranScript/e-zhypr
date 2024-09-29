## Configuration

The application reads configuration settings from `~/.config/e-zhypr/config.ini`. You can modify the following settings:

- `BASE_URL`: The base URL for the upload service.
- `GRIMBLAST_PATH`: Path to the Grimblast executable.
- `API_KEY`: Your API key for the upload service.
- `SAVE_DIRECTORY`: Directory to save screenshots.
- `IMAGE_FORMAT`: Format of the saved images (e.g., png, jpg).
- `VERBOSE`: Enable detailed output.

## Usage

To use the e-zhypr application, you can run the following commands in your terminal:

### Capture a Partial Screenshot

```bash
e-zhypr partial
```

### Capture a Full Screenshot

```bash
e-zhypr fullscreen
```


### Capture a Window Screenshot

```bash
e-zhypr window
```

### View Upload History

```bash
e-zhypr history
```


### Clear Upload History

```bash
e-zhypr clear
```


### Command Options

- `--file_name <filename>`: Specify the name of the file to save the screenshot.
- `--verbose`: Enable detailed output for debugging purposes.
- `--help`: Show help message and exit.

## Logging

Logs are saved to `e-zhypr.log` in the current directory. You can check this file for detailed information about the application's operations.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any improvements or bug fixes.

## Acknowledgments

- [Typer](https://typer.tiangolo.com/) for the command-line interface.
- [Rich](https://rich.readthedocs.io/en/stable/) for beautiful console output.
- [Pillow](https://python-pillow.org/) for image processing.
