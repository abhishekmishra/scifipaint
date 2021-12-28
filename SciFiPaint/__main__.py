from .SciFiPaint import get_config, window, run_app, get_args, run_command

if __name__ == "__main__":
    get_config()
    args = get_args()

    if args.filename:
        run_command("open_file", window, None, None, filename=args.filename)

    run_command("window_title", window, None, None)

    run_app()
