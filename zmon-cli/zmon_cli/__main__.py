from zmon_cli.main import main

if __name__ == '__main__':
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print('\nStopped by the user')
