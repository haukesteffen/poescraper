package main

type Poe struct {
	NextChangeID string     `json:"next_change_id"`
	Stashes      []PoeStash `json:"stashes"`
}

type PoeStash struct {
	ID                string    `json:"id" db:"stashid"`
	Public            bool      `json:"public"`
	AccountName       string    `json:"accountName" db:"accountname"`
	LastCharacterName string    `json:"lastCharacterName"`
	Stash             string    `json:"stash" db:"stash"`
	StashType         string    `json:"stashType"`
	League            string    `json:"league" db:"league"`
	Items             []PoeItem `json:"items"`
}

type PoeItem struct {
	Verified     bool   `json:"verified"`
	W            int    `json:"w"`
	H            int    `json:"h"`
	Icon         string `json:"icon"`
	StackSize    int    `json:"stackSize"`
	MaxStackSize int    `json:"maxStackSize"`
	League       string `json:"league"`
	Fractured    bool   `json:"fractured"`
	ID           string `json:"id"`
	Synthesised  bool   `json:"synthesised"`
	Name         string `json:"name"`
	TypeLine     string `json:"typeLine"`
	BaseType     string `json:"baseType"`
	Identified   bool   `json:"identified"`
	Ilvl         int    `json:"ilvl"`
	Corrupted    bool   `json:"corrupted"`
	Note         string `json:"note"`
	Properties   []struct {
		Name        string          `json:"name"`
		Values      [][]interface{} `json:"values"`
		DisplayMode int             `json:"displayMode"`
		Type        int             `json:"type"`
	} `json:"properties"`
	ImplicitMods  []string `json:"implicitMods"`
	ExplicitMods  []string `json:"explicitMods"`
	FracturedMods []string `json:"fracturedMods"`
	FlavourText   []string `json:"flavourText"`
	FrameType     int      `json:"frameType"`
	ArtFilename   string   `json:"artFilename"`
	Extended      struct {
		Category      string   `json:"category"`
		Subcategories []string `json:"subcategories"`
	} `json:"extended"`
	X           int    `json:"x"`
	Y           int    `json:"y"`
	InventoryID string `json:"inventoryId"`
}
