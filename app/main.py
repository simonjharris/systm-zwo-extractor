import shutil
import os
import re
from pathlib import Path

from fastapi import FastAPI, Query
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
import uvicorn

import suffersync

app = FastAPI()


def cleanup() -> None:
    """
    Files shouldn't persist between instances, but in case they do this will remove them.
    """
    if Path('zwo_files.zip').exists():
        os.remove('zwo_files.zip')
    if Path('zwo').exists():
        shutil.rmtree('zwo')


def reformat_files() -> None:
    """
    Some files have blank lines at the top, this will remove them.
    Files have 'commented out' tags on some lines e.g. <!-- abs power: 100 -->,
    these need to be removed or the files are rejected by RGT.
    """
    for file in os.listdir('zwo'):
        filepath = os.path.join('zwo', file)

        fileout = []
        with open(filepath, 'r') as f:

            for en, line in enumerate(f.readlines()):
                if en == 0 and line == '\n':
                    continue
                match = re.search(r'<!-- abs power: \d+ -->', line)
                if match:
                    fileout.append(line[:match.start()] + '\n')
                else:
                    fileout.append(line)

        # Check xml tag is present on first line
        if 'xml' not in fileout[0]:
            fileout.insert(0, '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n')

        # rewrite processed file
        with open(filepath, 'w') as f:
            f.writelines(fileout)


@app.get('/sufferfest')
async def get_zwo_files(systm_username: str = Query(None, alias='systm-username'),
                        systm_password: str = Query(None, alias='systm-password')
                        ) -> HTMLResponse or JSONResponse:

    # cleanup any files from previous requests
    cleanup()

    try:
        # Run suffersync script, will catch AttributeError for incorrect password
        suffersync.main(systm_username, systm_password)
    except AttributeError:
        return JSONResponse({'error': 'Incorrect SYSTM Username or Password'},
                            status_code=401)

    # check file format
    reformat_files()

    # zip all the files
    shutil.make_archive('zwo_files', 'zip', 'zwo')
    html = """
    <html>
        <head>
            <title>Download zwo files</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-1BmE4kWBq78iYhFldvKuhfTAU6auU8tT94WrHftjDbrCEXSU1oBoqyl2QvZ6jIW3" crossorigin="anonymous">
        </head>
        <body>
            <h1 style="text-align: center"><a href='/zwo_files'>Download</a></h1>
        </body>
    </html>
    """
    # return download link
    return HTMLResponse(html)


@app.get('/zwo_files')
async def return_files() -> FileResponse:
    return FileResponse('zwo_files.zip')


if __name__ == '__main__':
    cleanup()
    uvicorn.run(app, host='0.0.0.0', port=8080)
