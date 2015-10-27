#! /usr/bin/python3
"""
Interface html pour les évaluations de la résolution bib-findout
todo
les dossiers de Corpus de libconsulte et les pools du sampler
"""
from flask import Flask, render_template, request, redirect
from os import listdir, path, mkdir
from re import sub, MULTILINE, search
from json import load
from subprocess import check_output
from configparser import ConfigParser

# from libconsulte import api  # pour les requêtes directes


# APP exportable = ici (cf. main tout en bas)
mon_app = Flask(__name__)
mon_app.debug = True

script_dir = path.dirname(path.realpath(__file__))

# ----------------------------------------------------------------------
# fichier config : 

CONF = ConfigParser()
with open(path.join(script_dir,'ui.config')) as f:
	CONF.read_file(f)
# -----------------------------------------------------------------------------



# -----------------------------------------------------------------------------------
# prépa des fichiers d'évaluations + "next" : prochain doc à traiter via get_first
# recette / resultats de l'évaluation de résolution
RECETTE_DIR = CONF['evaluation_findout']['fixture_dir']         # requêtes testées
EVALDONE_DIR = CONF['evaluation_findout']['eval_results_dir']   # évaluations des requêtes testées

# pour les comparaisons
def my_bname(a_path):
	"""
	le basename sans l'extension .json (recettes) ou .fo_evals.tsv (résultats de formulaire)
	"""
	return sub("\.test_resolution\.json$|\.fo_evals\.tsv$","" ,path.basename(a_path))

# pour re-vérifier les dossiers lorsqu'on lance get_first_remaining
def recheck_todo_ids():
	return [my_bname(fi) for fi in listdir(RECETTE_DIR)]


def recheck_done_ids():
	return [my_bname(fi) for fi in listdir(EVALDONE_DIR)]


# pour actualiser le suivant
def get_first_remaining(todo_files, done_files):
	"""
	Appelé si on va sur /evaluation_findout sans préciser de doc
	
	Donne la première recette qui n'apparait pas dans les done_files
	"""
	if not len(done_files):
		# si aucun done
		return(todo_files[0])
	else:
		for rid in todo_files:
			if rid not in done_files:
				return rid
		# si tous done
		return None
# -----------------------------------------------------------------------------



# ------------------
#    R O U T E S
# ------------------
@mon_app.route('/')
def www_root():
	return redirect('/evaluation_docs')


@mon_app.route('/evaluation_docs')
def www_eval_docs():
	"""
	fait la liste des docs à traiter et propose de lancer le formulaire sur l'un d'entre eux
	"""
	
	doc_infos = []
	
	# on prépare la liste en annotant : nom + fait/pas fait
	recette_ids = recheck_todo_ids()
	
	done_ids = recheck_done_ids()
	
	print("===\nTODO", recette_ids)
	print("===\nDONE", done_ids)
	
	for rid in recette_ids:
		# todo un hash pour lookup + efficace
		doc_infos.append({"name":rid,"ok":(rid in done_ids)})
		#                               -------------------
		#                                     booléen
	
	print("===\nDOC_INFOS", doc_infos)
	
	return render_template(
	   'list_bibfiles.html', 
	   recette_docs=doc_infos, 
	   page_active="evaluation_docs"
	   )

@mon_app.route('/evaluation_findout')
def www_eval_fo():
	"""
	formulaire d'évaluation findout pour un doc
	"""
	if not len(request.args) or 'docname' not in request.args:
		next_doc = get_first_remaining(todo_files=recheck_todo_ids(), done_files=recheck_done_ids())
		if next_doc:
			return redirect('/evaluation_findout?docname=%s' % next_doc)
		else:
			return("<h3>Tous les documents du dossier %s ont été traités :)</h3>" % RECETTE_DIR)
	else:
		# todo tester l'input
		docname = request.args.get("docname")
		
		# sans extension
		# print("DOCNAME", docname)
		
		recette_doc = path.join(RECETTE_DIR, docname+".test_resolution.json")
		recette = open(recette_doc, "r")
		bibinfos = load(recette)
		recette.close
		
		return render_template(
		   'eval_bibs.html', 
		   did=my_bname(docname),
		   refbibs=bibinfos,
		   page_active="evaluation_findout")


@mon_app.route('/evaluation_findout', methods=['POST'])
def www_eval_fo_post():
	"""
	Pour les retours enregistrés
	
	forme d'évaluation:
	-------------------
	qid = doc_id + bib_id + q-methode_id
	
	forme d'enregistrement:
	------------------------
	fichier: doc_id.fo_evals.tsv
	  lignes: bib_id
	  colonnes: q-methode_id
	
	"""
	# debug
	# return("<p>everything:%s</p><p>req:%s</p>" % (str([(k,request.form[k]) for k in request.form]),dir(request),))
	
	# préparation dossier
	if not path.isdir(EVALDONE_DIR):
		mkdir(EVALDONE_DIR)
	
	# identifiant du document caché dans le formulaire -------
	did = request.form['doc_id']
	
	# sauvegarde des remarques à part ------------------------
	remarques_lines = []
	for k in request.form:
		if search('remarques$',k) and len(request.form[k]):
			# 2 lignes id ex: "#b1-remarques:" + soulignement
			remarques_lines += ['#' + k + ":", "---------------"]
			# contenu de la remarque (texte libre + saut ligne vide)
			remarques_lines += [request.form[k],'']
	
	log_remarques = open(path.join(EVALDONE_DIR, did+".remarques.txt"), "w")
	log_remarques.write("\n".join(remarques_lines)+"\n")
	log_remarques.close()
	
	# sauvegarde pour les évaluations proprement dites -------
	# (1) on re-charge grace au champ 'doc_id' du formulaire
	recette_doc = path.join(RECETTE_DIR, did+".test_resolution.json")
	recette = open(recette_doc, "r")
	bibinfos = load(recette)
	recette.close
	# ... afin d'avoir les bon ids
	
	# (2) on parcourt en écrivant un fichier pour ce doc
	header = 'bib_id\tq0\tq1\tq2\tq3\tq4\tq5\tq6\tq7'
	output_lines = [header]
	
	for bibinfo in bibinfos:
		
		if did != bibinfo['parent_doc']:
			# ne devrait jamais arriver
			raise KeyError("mismatch!")
		
		bid = bibinfo['bib_id']
		
		this_line = [bid]
		
		# on va faire une colonne par requête
		# => on veut qu'il y en ait toujours le même nombre
		n_q = len(bibinfo['solved_qs'])
		
		if n_q != 8:
			# raise TypeError("nombre de requêtes: %i != 8" % n_q)
			print("(skip):%s" % bibinfo['findout_errs'])
			continue
		
		for i, bbq_infos in enumerate(bibinfo['solved_qs']):
			# nos identifiants doivent être ici comme dans le formulaire
			qid = did+".bib"+bid+".qmeth"+str(i)
			
			# on vérifie ce qu'il y a dans le formulaire pour cette requêtes
			if qid in request.form:
				this_line.append("1")
			else:
				this_line.append("0")
		
		output_lines.append("\t".join(this_line))
	
	out_doc = path.join(EVALDONE_DIR, did+".fo_evals.tsv")
	with open(out_doc, "w") as out:
		out.write("\n".join(output_lines))
	
	
	# debug:
	# print("données brutes: %s" % request.form)
	
	return("""
<html>
	<body>
		<h3>données bien enregistrées en tableau</h3>
		<p>fichier: %s</p>
		<p>Retourner au <a href="/evaluation_docs">documents à traiter</a></p>
	</body>
</html>
""" % out_doc)


# pour tester la template mère -----------

@mon_app.route('/test_base')
def www_ird():
	return render_template('ird_base.html')

@mon_app.route('/test_hyphe')
def www_hyphe():
	return render_template('hyphe.html')



# petits essais GUI ----------------------

@mon_app.route('/exemplier')
def www_showcase():
	return render_template('showcase_pdf_wall.html', page_active="exemplier")

@mon_app.route('/treemap')
def www_treemapbig():
	return render_template('treemap.html', page_active="treemap")


@mon_app.route('/navi_graph')
def www_navigraph():
	return render_template('navi_graph.html', page_active="navi_graph")


@mon_app.route('/ls')
def www_ls():
	hello_str = "<h3>hello</h3><br/>"
	liste_str = check_output(['ls', '-l']).decode('UTF-8')       # si windows => liste_str = listdir('.')
	
	html = hello_str + '<p style="font-family: Monospace">' + sub(' ', '&nbsp;', sub('\n', '<br/>', liste_str)) + '</p>'
	return html


if __name__ == '__main__':
	mon_app.run()
