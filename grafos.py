import networkx as nx
import matplotlib.pyplot as plt
from pymongo import MongoClient
import tkinter as tk
from tkinter import messagebox
import community as community_louvain  

G = nx.DiGraph()

client = MongoClient("mongodb://localhost:27017/")
db = client["recomendacion_contenido"]

usuarios = {doc["_id"]: doc["nombre"] for doc in db.Usuarios.find()}
artistas = {doc["_id"]: doc["nombre"] for doc in db.Artistas.find()}

for u in usuarios:
    G.add_node(u, tipo="usuario")
for a in artistas:
    G.add_node(a, tipo="contenido")

for doc in db.Interacciones.find():
    G.add_edge(doc["usuario_id"], doc["artista_id"], weight=doc["peso"])

def recomendar_artista(G, usuario, numero_recomendaciones=10):
    vistos = set(G.successors(usuario))
    puntajes = {}

    for otro_usuario in G.nodes:
        if str(otro_usuario).startswith("U") and otro_usuario != usuario:
            for contenido in G.successors(otro_usuario):
                if contenido not in vistos:
                    peso = G[otro_usuario][contenido].get("weight", 1)
                    puntajes[contenido] = puntajes.get(contenido, 0) + peso

    recomendaciones = sorted(puntajes.items(), key=lambda x: x[1], reverse=True)
    return [c for c, _ in recomendaciones[:numero_recomendaciones]]


def visualizar_grafo(G, titulo="Grafo de Recomendaciones"):
    pos = {}
    vertical_spacing = 1
    horizontal_spacing = 0.5

    usuarios_ = [n for n in G.nodes if str(n).startswith("U")]
    for i, u in enumerate(usuarios_):
        pos[u] = (0, -i * vertical_spacing)

    artistas_ = [n for n in G.nodes if str(n).startswith("C")]
    for i, c in enumerate(artistas_):
        pos[c] = (horizontal_spacing, -i * vertical_spacing)

    height = max(len(usuarios_), len(artistas_)) * vertical_spacing * 0.3
    plt.figure(figsize=(20, height))

    nx.draw(
        G, pos, with_labels=True, node_color="pink", node_size=1500,
        font_size=9, font_weight='bold', edge_color='gray'
    )

    edge_labels = nx.get_edge_attributes(G, 'weight')
    nx.draw_networkx_edge_labels(
        G, pos, edge_labels=edge_labels, font_size=7
    )

    plt.title(titulo)
    plt.axis("off")
    plt.tight_layout()
    plt.show()

def detectar_comunidades(G):
    G_undirected = G.to_undirected()
    partition = community_louvain.best_partition(G_undirected)
    return partition

def calcular_centralidad(G):
    return nx.degree_centrality(G)

def mostrar_comunidades_tk():
    partition = detectar_comunidades(G)
    nombres_completos = {**usuarios, **artistas}
    comunidades = {}
    for nodo, com in partition.items():
        comunidades.setdefault(com, []).append(nombres_completos.get(nodo, nodo))

    texto = ""
    for com, nodos in comunidades.items():
        texto += f"Comunidad {com}:\n"
        for n in nodos:
            texto += f"  - {n}\n"
        texto += "\n"

    messagebox.showinfo("Comunidades Detectadas", texto)

def mostrar_centralidad_tk():
    centralidad = calcular_centralidad(G)
    nombres_completos = {**usuarios, **artistas}
    top_nodos = sorted(centralidad.items(), key=lambda x: x[1], reverse=True)[:10]

    texto = "Top 10 nodos por centralidad de grado:\n"
    for nodo, val in top_nodos:
        texto += f"  - {nombres_completos.get(nodo, nodo)}: {val:.4f}\n"

    messagebox.showinfo("Centralidad de Nodos", texto)

def ejecutar_recomendacion():
    usuario_actual = entry_usuario.get().strip()
    if usuario_actual not in usuarios:
        messagebox.showerror("Error", f"El usuario '{usuario_actual}' no existe.")
        return

    recomendados = recomendar_artista(G, usuario_actual)
    text_resultado.delete("1.0", tk.END)

    if not recomendados:
        text_resultado.insert(tk.END, "(No hay recomendaciones disponibles)\n")
    else:
        for contenido_id in recomendados:
            nombre_artista = artistas.get(contenido_id, contenido_id)
            text_resultado.insert(tk.END, f"- {nombre_artista}\n")
    visualizar_grafo(G)

ventana = tk.Tk()
ventana.title("Recomendador de Artistas")

label = tk.Label(ventana, text="Ingrese ID del Usuario:")
label.pack(pady=5)

entry_usuario = tk.Entry(ventana, width=30)
entry_usuario.pack(pady=5)

btn = tk.Button(ventana, text="Recomendar", command=ejecutar_recomendacion)
btn.pack(pady=5)

btn_comunidades = tk.Button(ventana, text="Mostrar Comunidades", command=mostrar_comunidades_tk)
btn_comunidades.pack(pady=5)

btn_centralidad = tk.Button(ventana, text="Mostrar Centralidad", command=mostrar_centralidad_tk)
btn_centralidad.pack(pady=5)

text_resultado = tk.Text(ventana, width=60, height=10)
text_resultado.pack(pady=10)

ventana.mainloop()
