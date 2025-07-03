Даже с другого origin'а (localhost:8001) iframe может собирать фингерпринт (через external-fp.js) и отображать его внутри себя.\
Родительская страница не может напрямую прочитать содержимое iframe (из-за политики Same-Origin Policy).\
Но визуально iframe может отобразить фингерпринт — Chrome и Safari отдали разные значения userAgent, colorDepth, language и т.д.