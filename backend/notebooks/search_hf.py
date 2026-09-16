from huggingface_hub import HfApi

api = HfApi()
print("Searching datasets for 'hindi'...")
hindi_datasets = list(api.list_datasets(search="hindi", limit=10))
for d in hindi_datasets:
    print(d.id)

print("\nSearching datasets for 'telugu'...")
telugu_datasets = list(api.list_datasets(search="telugu", limit=10))
for d in telugu_datasets:
    print(d.id)

print("\nSearching datasets for 'common_voice'...")
cv_datasets = list(api.list_datasets(search="common_voice", limit=10))
for d in cv_datasets:
    print(d.id)
