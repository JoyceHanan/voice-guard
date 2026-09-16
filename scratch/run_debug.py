import sys
import os
import traceback

sys.path.insert(0, os.path.abspath('backend'))
sys.path.insert(0, os.path.abspath('backend/notebooks'))

error_file = "scratch/error.txt"

try:
    print("Importing prepare_and_train_v2...", flush=True)
    import prepare_and_train_v2 as pt
    print("Starting Task 1...", flush=True)
    pt.run_task_1()
    print("Starting Task 2...", flush=True)
    model, unfrozen = pt.run_task_2()
    print("Starting Task 3 & 4...", flush=True)
    pt.run_task_3_and_4(model)
    print("ALL TASKS FINISHED SUCCESSFULLY!", flush=True)
except Exception as e:
    with open(error_file, "w") as f:
        traceback.print_exc(file=f)
    print("EXCEPTION OCCURRED! Written to scratch/error.txt", flush=True)
    traceback.print_exc()
