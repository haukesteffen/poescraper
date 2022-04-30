from utils import fetch, train_model

def main():
    if fetch(1529423):
        return
    train_model()


if __name__ == "__main__":
    main()


###TODO
# load data in chunks to save memory
