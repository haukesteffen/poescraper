package main

import (
	b64 "encoding/base64"
	"fmt"
	"io"
	"net/http"
	"strings"
)

func main() {
	priceCheckBackendURL := "http://pricelearner:8081"
	//priceCheckBackendURL = "http://pricelearner.wfwfwf.wf"
	fmt.Printf("Starting server at port 8080\n")
	http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		http.ServeFile(w, r, "index.html")
	})
	http.HandleFunc("/fetch", func(w http.ResponseWriter, r *http.Request) {
		reqItem, _ := io.ReadAll(r.Body)
		reqItemStr := string(reqItem[:])
		fmt.Println("Request item:", reqItemStr)

		req, err := http.NewRequest("POST", priceCheckBackendURL, strings.NewReader(reqItemStr))
		if err != nil {
			// handle err
		}
		req.Header.Set("Content-Type", "application/x-www-form-urlencoded")

		resp, err := http.DefaultClient.Do(req)
		if err != nil {
			// handle err
		}
		defer resp.Body.Close()

		fmt.Println(resp.Request.Body)

		fff, _ := b64.StdEncoding.DecodeString(string(reqItem[:]))
		fmt.Println("send conv:", string(fff))
		body, _ := io.ReadAll(resp.Body)
		bodyString := string(body)
		fmt.Println("Est. price:", bodyString)
		txtHTML := bodyString + " Chaos"
		io.WriteString(w, txtHTML)
	})
	if err := http.ListenAndServe(":8080", nil); err != nil {
		panic(err)
	}
}
