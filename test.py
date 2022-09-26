from tqdm import tqdm

pbar = tqdm(total=100)
pbar.update(25)
pbar.update(n=10)
pbar(position=10)