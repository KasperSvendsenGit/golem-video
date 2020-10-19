#!/usr/bin/env python3
import asyncio
import pathlib
import sys

import yapapi
from yapapi.log import enable_default_logger, log_summary, log_event_repr  # noqa
from yapapi.runner import Engine, Task, vm
from yapapi.runner.ctx import WorkContext
from datetime import timedelta
import requests
import subprocess

# For importing `utils.py`:
script_dir = pathlib.Path(__file__).resolve().parent
parent_directory = script_dir.parent
sys.stderr.write(f"Adding {parent_directory} to sys.path.\n")
sys.path.append(str(parent_directory))
import utils  # noqa

def update_status(job: str, status: str):
    if "-" in job:
        subprocess.Popen(["wget", "-O/dev/null", "-q", f"http://localhost:5000/status/set/{job}/{status}"])

async def main(subnet_tag: str, presets: str, input_file: str, job: str):
    package = await vm.repo(
        image_hash="9a6b2409ccd96b3352b3fcdc6e1e568bdfa4d4e258589cfaff084786",
        min_mem_gib=0.5,
        min_storage_gib=2.0,
    )

    preset_list = list(filter(str.strip, presets.split(",")))

    async def worker(ctx: WorkContext, tasks):
        sent_file = "/golem/resource/input.file"
        ctx.send_file(input_file, sent_file)

        async for task in tasks:
            preset = task.data

            if "MKV" in preset or preset == "Roku 2160p60 4K HEVC Surround":
                output_ext = ".mkv"
            else:
                output_ext = ".mp4"

            subjob = f"{job}_{preset_list.index(preset)+1}"

            update_status(subjob, "starting")

            output_file = f"{subjob}{output_ext}"

            ctx.log(f"job: {subjob}")

            update_status(subjob, "job sent")
            
            commands = (
                'cd /golem/output; '
                f'echo preset:{preset} > log.txt; '
                f'echo output_file:{output_file} >> log.txt; '
                f"HandBrakeCLI -i {sent_file} -o {output_file} --preset '{preset}' >> log.txt 2>&1; "
                'ls -lah >> log.txt'
            )
            
            ctx.run("/bin/sh", "-c", commands)

            #ctx.download_file(f"/golem/output/log.txt", "log.txt")
            ctx.download_file(f"/golem/output/{output_file}", f"./downloads/{output_file}")

            yield ctx.commit()            

            update_status(subjob, "done")

            # TODO: Check if job results are valid
            # and reject by: task.reject_task(reason = 'invalid file')
            task.accept_task(result=output_file)

        ctx.log("no more videos to convert!")

    init_overhead: timedelta = timedelta(minutes=7)



    # By passing `event_emitter=log_summary()` we enable summary logging.
    # See the documentation of the `yapapi.log` module on how to set
    # the level of detail and format of the logged information.
    async with Engine(
        package=package,
        max_workers=10,
        budget=20.0,
        timeout=init_overhead,
        subnet_tag=subnet_tag,
        event_emitter=log_summary(log_event_repr),
    ) as engine:

        async for task in engine.map(worker, [Task(data=preset) for preset in preset_list]):
            print(
                f"{utils.TEXT_COLOR_CYAN}"
                f"Task computed: {task}, result: {task.output}"
                f"{utils.TEXT_COLOR_DEFAULT}"
            )


if __name__ == "__main__":
    parser = utils.build_parser("Video Transcoder")
    parser.add_argument(
        "--presets", default="Fast 480p30", help="HandBrakeCLI transcode preset; can pass multiple separated by comma; default: %(default)s"
    )
    parser.add_argument(
        "--job", default="0", help="An optional job ID; default: %(default)s"
    )
    parser.add_argument("input_file")
    args = parser.parse_args()

    enable_default_logger(log_file=args.log_file)
    loop = asyncio.get_event_loop()
    subnet = args.subnet_tag
    sys.stderr.write(
        f"yapapi version: {utils.TEXT_COLOR_YELLOW}{yapapi.__version__}{utils.TEXT_COLOR_DEFAULT}\n"
    )
    sys.stderr.write(f"Using subnet: {utils.TEXT_COLOR_YELLOW}{subnet}{utils.TEXT_COLOR_DEFAULT}\n")
    task = loop.create_task(main(subnet_tag=args.subnet_tag, input_file=args.input_file, presets=args.presets, job=args.job))
    try:
        asyncio.get_event_loop().run_until_complete(task)

    except (Exception, KeyboardInterrupt) as e:
        print(e)
        task.cancel()
        asyncio.get_event_loop().run_until_complete(task)
