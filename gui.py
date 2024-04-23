# Usage: python3 gui.py <elasticsearch_host> <elasticsearch_api_key> <elasticsearch_index>

import sys
import tkinter as tk
import webbrowser
from elasticsearch import Elasticsearch

results = None

def search(query):
    global results
    results = client.search(index=sys.argv[3], q=query, size=20)['hits']['hits']

def show_results():
    results_box.delete(0, tk.END)
    article_preview_text.delete(1.0, tk.END)
    for hit in results:
        results_box.insert(tk.END, hit['_source']['title'])

def update_button_state():
    new_state = tk.NORMAL if results_box.curselection() else tk.DISABLED
    actions_like.config(state=new_state)
    actions_dislike.config(state=new_state)
    actions_open_webpage.config(state=new_state)

def on_search():
    search(search_box.get())
    show_results()
    update_button_state()

def on_select(_):
    article_preview_text.delete(1.0, tk.END)
    if results_box.curselection():
        article_preview_text.insert(tk.END, results[results_box.curselection()[0]]['_source']['body_content'])
    update_button_state()

def on_open_webpage():
    webbrowser.open(results[results_box.curselection()[0]]['_source']['url'])

def on_like():
    print("Like")

def on_dislike():
    print("Dislike")

client = Elasticsearch(sys.argv[1], api_key=sys.argv[2])

root = tk.Tk()
root.title("Search")
root.geometry("400x600")
root.minsize(300, 500)

main_frame = tk.Frame(root, padx=10, pady=10)

search_frame = tk.Frame(main_frame, padx=5, pady=5)
search_box = tk.Entry(search_frame)
search_button = tk.Button(search_frame, text="Search", command=on_search)
search_box.bind("<Return>", lambda _: on_search())
search_box.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
search_button.pack(side=tk.RIGHT)
search_frame.pack(fill=tk.X)

results_frame = tk.Frame(main_frame, padx=5, pady=5)
results_scrollbar = tk.Scrollbar(results_frame)
results_box = tk.Listbox(results_frame, yscrollcommand=results_scrollbar.set)
results_scrollbar.config(command=results_box.yview)
results_box.bind("<<ListboxSelect>>", on_select)
results_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
results_box.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
results_frame.pack(fill=tk.BOTH, expand=True)

actions_frame = tk.Frame(main_frame, padx=5, pady=5)
actions_like = tk.Button(actions_frame, text="Like", command=on_like)
actions_dislike = tk.Button(actions_frame, text="Dislike", command=on_dislike)
actions_open_webpage = tk.Button(actions_frame, text="Open Webpage", command=on_open_webpage)
actions_like.config(state=tk.DISABLED)
actions_dislike.config(state=tk.DISABLED)
actions_open_webpage.config(state=tk.DISABLED)
actions_like.pack(side=tk.LEFT)
actions_dislike.pack(side=tk.LEFT)
actions_open_webpage.pack(side=tk.RIGHT)
actions_frame.pack(fill=tk.X)

article_preview_frame = tk.Frame(main_frame, padx=5, pady=5)
article_preview_header = tk.Label(article_preview_frame, text="Article Preview")
article_preview_scrollbar = tk.Scrollbar(article_preview_frame)
article_preview_text = tk.Text(article_preview_frame, yscrollcommand=article_preview_scrollbar.set)
article_preview_scrollbar.config(command=article_preview_text.yview)
article_preview_header.pack()
article_preview_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
article_preview_text.pack(fill=tk.BOTH, expand=True)
article_preview_frame.pack(fill=tk.BOTH, expand=True)

main_frame.pack(fill=tk.BOTH, expand=True)

root.mainloop()
