<p>
  Русский | English
</p>
<p>
  Итак, у вас есть Ubuntu, но у нее нет доступа в интернет. Вы хотите просто написать программку на питоне и вам понадобилась какая-либо библиотека. Ее можно спокойно скачать на сторонней машине через пакетный менеджер питона и далее ее можно установить через пакетный менеджер pip на нашей закрытой от интернета Ubuntu. Но в Ubuntu по умолчанию в python не установили pip. Помощь в интернете для решения этой тривиальной проблемы затянет вас часа на 2, или 4, или вообще несколько дней.
</p>
<p>
  У ubuntu есть сайт packages.ubuntu.com. Этот сайт держит ссылки на все библиотеки Ubuntu. Но скачивать оттуда библиотеку с зависимостями вас заставляют ручками, что очень неудобно.
</p>
<p>
  Эта программа является скраппером библиотек с этого сайта. Захотели скачать python3.10-venv? Зашли на packages.ubuntu.com, нашли там стартовую библиотеку, которую вы хотите скачать, копируете из браузера ссылку и вставляете в эту программу. Ждете, пока программа отработает - и вуаля! Нужный вам пакет и все его 64 зависимости скачаны в формате .deb! Переносите их на изолированную машину и <code>sudo dpkg -i *.deb</code> их (сначала запакуйте для удобства в какой-нибудь zip)!
</p>
<p>
  Я сравнил вывод этой программы с результатом <code>apt-cache depends --recurse --no-recommends --no-suggests --no-conflicts --no-breaks --no-replaces --no-enhances xrdp</code> (спасибо panticz с stackoverflow за ответ на вопрос 13756800) и вывод этой программы совпал по количеству файлов. Некоторые файлы называются по другому, потому что ubuntu при загрузке зачем-то в названия файлов пихает всякие "1%3a" или "2%3a". А так, все работает.
</p>
<p>
  Этот скрипт работает на питоне, так что это решение для загрузки пакетов для ubuntu офлайн через системы типа других линуксов с другими пакетными менеджерами и винды. Потому что бывает так, что под рукой нет ubuntu с выходом в интернет для офлайн загрузки этих пакетов и packages.ubuntu.com является буквально единственным способом скачать пакеты.
</p>
<p>
  Прикрутил внутрь argparse, где расписал принимаемые мной аргументы.
</p>
<p>
  При разработке обновления и адекватного рабочего состояния программы обнаружил, что на этом сайте зачем-то пишут, мол у библиотеки есть 5+ реализаций под все платформы, но когда заходишь для скачивания - там пусто. Внезапно. Пакеты amd64 есть, а они в основном единственные нужны. 
</p>

<p>
  Пример команды:
</p>
<pre>python UbuntuPckgLoader.py https://packages.ubuntu.com/jammy-updates/xrdp</pre>


<p>English</p>

<p>
  Say, you have Ubuntu, but it doesn't have access to internet. You just want to write some simple python script and you require some library. You can download it on different machine using python package manager and then install it offline using pip here. But Ubuntu desktop 22.04, which you are currently using, does not have preinstalled pip, because god forbid, it's like you need 66 packages to install and 30MB in size! It's clearly too big for 4,43GB image to have python3-pip preinstalled 😠 The whole ordeal to solve this hassle will take 2 hours, maybe 4, maybe even a day, or two... the problem, that's literally can be solved if there was any way to automatically collect this packages with all of it dependencies on machines, that does not have ubuntu, but have access to internet.
</p>
<p>
  Ubuntu have a website packages.ubuntu.com that hosts links to ubuntu libraries. But it doesn't have automated tool to like get needed library and collect all of it dependecies. They discourage you from using this site and recommend you to use package manager, because everybody have ubuntu, connected to internet. It's not like, only 4% computers in the world are linux-bases of which the are a third of ubuntu, everybody have ubuntu with internet, of course!
</p>
<p>
  Anyway, this program is a python script that scraps that website for library, that you need. It loads all of the dependencies of said package and said package itself, which you could later transfer to isolated machine, where you can <code>dpkg -i *.deb</code> them all. It seems you need to do it (<code>dpkg -i *.deb</code>) until all errors stops, because it's not very happy about installing everything at once...
</p>
<p>
  I checked this program' output with the output of <code>apt-cache depends --recurse --no-recommends --no-suggests --no-conflicts --no-breaks --no-replaces --no-enhances xrdp</code> (my thanks to panticz from stackoverflow for his answer for question 13756800) and the output is exact in numbers of packages. Some files differ in names, because ubuntu on load for some reason puts there some "1%3a" or "2%3a", but apart from that, everything is working.
</p>
<p>
  It's a python script, so you can run it anywhere, where you have a python, like in debian or windows.
</p>
<p>
  I also added argparse, where i written all accepted arguments.
</p>
<p>
  While developing update found out that this website for some unknown reason writes that package has like 5+ platform versions, but when you try to check it out, they happen to just not have load links. I... didn't expect this. Well, they have amd64 packages and they mostly the only ones you need. But it's very strange, are they aware of it? Is it supposed to be so? Doubt it. But to report bug on their website, they require registration, so i'm out.
</p>

<p>
  Here is the list of architectures for https://packages.ubuntu.com/jammy/libc6, green = there is download link, red = there is none:
</p>

```diff
+ amd64
- arm64
- armhf
+ i386
- ppc64el
- riscv64
- s390x
```

<p>
  Usage example:
</p>
<pre>python UbuntuPckgLoader.py https://packages.ubuntu.com/jammy-updates/python3.10-venv</pre>
<pre>python UbuntuPckgLoader.py https://packages.ubuntu.com/jammy-updates/python3-pip</pre>
