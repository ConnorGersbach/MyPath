#!/usr/bin/python3

import sys
import math
import collections
from lxml import etree
from PIL import Image, ImageDraw


class Node:
	def __init__(self, attrib):
		self.attrib = attrib
	
	def __str__(self):
		return str(self.attrib)

class Way:
	def __init__(self, attrib, nd):
		self.attrib = attrib
		self.nd = nd

	def __str__(self):
		return str(self.attrib) + "\n" + str(self.nd)


class OSM_Map:
	'''
	Parses osmFile, populates dictionaries, and creates image
	highways = dictionary of ways that are highways, indexed by the way id
	adjacency = adjacency list representing the adjacent nodes on highways, indexed by node id
	nodes = dictionary of nodes whose id appear in adjacency i.e. nodes that form highways, indexed by node id
	bounds = dictionary of the first bounds found in the osm map
	'''
	def __init__(self, osmFileName):
		self.highways = {}
		self.adjacency = {}
		self.nodes = {}
		self.bounds = {}
		self.img = Image.new("RGB",(1000,1000),(255,255,255))

		nodes_list = []
		
		try:
			doc = etree.parse(osmFileName)

			self.bounds = doc.findall("bounds")[0].attrib

			for way in doc.findall("way"):
				for tag in way.findall("tag"):
					if tag.attrib['k'] == "highway" and way.attrib["id"] not in self.highways:
						for nd in way.findall("nd"):
							nodes_list.append(nd.get("ref"))
							self.add_adjacency(nodes_list)
						self.highways[way.attrib["id"]] = Way(way.attrib, nodes_list)
						nodes_list = []

			for key in self.adjacency:
				for node in doc.xpath("//node[@id = '%s']" % key):
					self.nodes[node.get("id")] = Node(node.attrib)

			self.draw_highways()

		except IOError:
			print("Could not open file:", osmFileName)

	'''
	Helper method used by __init__ to create the adjacency list
	Adds an edge between the newly added node and the previous node
	'''
	def add_adjacency(self, nodes_list):
		if len(nodes_list) > 1:
			if not self.adjacency.get(nodes_list[-2]):
				self.adjacency[nodes_list[-2]] = {nodes_list[-1]}
			else:
				self.adjacency[nodes_list[-2]].add(nodes_list[-1])

			if not self.adjacency.get(nodes_list[-1]):
				self.adjacency[nodes_list[-1]] = {nodes_list[-2]}
			else:
				self.adjacency[nodes_list[-1]].add(nodes_list[-2])

	'''
	Helper method used to draw paths
	Scales the lon and lat of the nodes along the path 
	to the constant dimensions of the image
	'''
	def draw(self, road, colors, thickness = 3):
		coordinates = []
		draw = ImageDraw.Draw(self.img)
		for node_id in road:
			lon = float(self.nodes[node_id].attrib.get("lon"))
			lat = float(self.nodes[node_id].attrib.get("lat"))
			lon = math.floor((999*(lon-float(self.bounds["minlon"]))) / (float(self.bounds["maxlon"]) - float(self.bounds["minlon"])))
			lat = math.floor((999*(lat-float(self.bounds["minlat"]))) / (float(self.bounds["maxlat"]) - float(self.bounds["minlat"])))
			if(0 < lon < 999) and (0 < lat < 999):
				coordinates.append((lon,lat))
		draw.line(coordinates, colors, thickness)

	'''
	Helper method used by __init__ to draw all the highways
	Simply calls draw() on the nodes list of the various highways
	'''
	def draw_highways(self):
		for key in self.highways:
			self.draw(self.highways[key].nd, (150,150,150))
			

	'''
	Calls a bfs search to determine the shortest path 
	between src and dest
	'''
	def Route(self, src, dest):
		route = []
		try:
			route = self.bfs(src, dest)
		except KeyError:
			print("Invalid node id entered")

		self.draw(route,(50,50,50))

	'''
	Simple bfs algorithm using an adjacency list
	'''
	def bfs(self, src, dest):
		seen, queue = set([src]), collections.deque([src])
		parent = {}
		parent[src] = None

		if dest not in self.adjacency:
			raise KeyError

		while queue:
			vertex = queue.popleft()
			if vertex == dest:
				return self.backtrace(vertex,parent)
			for node_id in self.adjacency[vertex]:
				if node_id not in seen:
					parent[node_id] = vertex
					queue.append(node_id)
			seen.add(vertex)

	'''
	Helper method to bfs to perform the backtrace 
	and return the final route
	'''
	def backtrace(self, dest, parent):
		route = [dest]
		currNode = dest
		while parent[currNode] != None:
			route.append(parent[currNode])
			currNode = parent[currNode]
		return route[::-1]
		
	def Show(self):
		self.img.show()

	def Save(self, imgName):
		self.img.save(imgName)


def main(node_id1, node_id2, osmFileName = "map.osm", imgName = "output.pgm"):
	mp = OSM_Map(osmFileName)
	mp.Route(node_id1, node_id2)
	#mp.Show()
	mp.Save(imgName)

if __name__ == "__main__":
	try:
		main(*sys.argv[1:])
	except TypeError as e:
		if str(e)[:14] != "main() missing":
			raise
		else:
			print("Too few command line arguments. Usage: \n./mypath.py node_id1 node_id2[ osmFileName = \"map.osm\"[ imgName = \"output.pgm\"]]")