package api

type Poe struct {
	NextChangeID string `json:"next_change_id"`
	Stashes      []struct {
		ID                string    `json:"id"`
		Public            bool      `json:"public"`
		AccountName       string    `json:"accountName"`
		LastCharacterName string    `json:"lastCharacterName"`
		Stash             string    `json:"stash"`
		StashType         string    `json:"stashType"`
		League            string    `json:"league"`
		Items             []PoeItem `json:"items"`
	} `json:"stashes"`
}

type PoeItem struct {
	Verified     bool   `json:"verified"`
	W            int    `json:"w"`
	H            int    `json:"h"`
	Icon         string `json:"icon"`
	StackSize    int    `json:"stackSize"`
	MaxStackSize int    `json:"maxStackSize"`
	League       string `json:"league"`
	ID           string `json:"id"`
	Name         string `json:"name"`
	TypeLine     string `json:"typeLine"`
	BaseType     string `json:"baseType"`
	Identified   bool   `json:"identified"`
	Ilvl         int    `json:"ilvl"`
	Note         string `json:"note"`
	Properties   []struct {
		Name        string          `json:"name"`
		Values      [][]interface{} `json:"values"`
		DisplayMode int             `json:"displayMode"`
		Type        int             `json:"type"`
	} `json:"properties"`
	ImplicitMods []string `json:"inplicitMods"`
	ExplicitMods []string `json:"explicitMods"`
	FlavourText  []string `json:"flavourText"`
	FrameType    int      `json:"frameType"`
	ArtFilename  string   `json:"artFilename"`
	Extended     struct {
		Category      string   `json:"category"`
		Subcategories []string `json:"subcategories"`
	} `json:"extended"`
	X           int    `json:"x"`
	Y           int    `json:"y"`
	InventoryID string `json:"inventoryId"`
}
