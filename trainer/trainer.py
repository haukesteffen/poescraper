from utils import create_lexicon, fetch, create_new_model, train_model
import time

def main():
    itembase='amulet'
    create_lexicon(itembase=itembase)
    fetch(itembase=itembase, start_id=0)
    create_new_model(itembase=itembase)

    for i in range(10):
        if fetch(itembase=itembase) is not 1:
            train_model(itembase=itembase)
        time.sleep(300)


if __name__ == "__main__":
    main()


###TODO
# load data in chunks to save memory
