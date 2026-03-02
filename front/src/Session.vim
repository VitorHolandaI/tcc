let SessionLoad = 1
let s:so_save = &g:so | let s:siso_save = &g:siso | setg so=0 siso=0 | setl so=-1 siso=-1
let v:this_session=expand("<sfile>:p")
silent only
silent tabonly
cd ~/git/tcc/front/src
if expand('%') == '' && !&modified && line('$') <= 1 && getline(1) == ''
  let s:wipebuf = bufnr('%')
endif
let s:shortmess_save = &shortmess
if &shortmess =~ 'A'
  set shortmess=aoOA
else
  set shortmess=aoO
endif
badd +70 App.tsx
badd +105 ~/git/tcc/front/src/pages/DashboardAluno.tsx
badd +26 ~/git/tcc/back/app/main.py
badd +14 ~/git/tcc/back/app/controllers/submissao_controller.py
badd +11 ~/git/tcc/back/app/schemas/prova_schema.py
badd +1 ~/git/tcc/back/app/schemas/questao_schema.py
badd +97 ~/git/tcc/back/app/controllers/questao_controller.py
badd +31 ~/git/tcc/back/app/core/auth_dependency.py
badd +1 ~/git/tcc/back/run.py
badd +179 components/TextBox.tsx
badd +284 ~/git/tcc/back/app/core/ownership.py
badd +0 ~/git/tcc/front/src/services/SubmissaoService.ts
argglobal
%argdel
$argadd App.tsx
edit ~/git/tcc/front/src/services/SubmissaoService.ts
argglobal
balt components/TextBox.tsx
setlocal foldmethod=manual
setlocal foldexpr=0
setlocal foldmarker={{{,}}}
setlocal foldignore=#
setlocal foldlevel=0
setlocal foldminlines=1
setlocal foldnestmax=20
setlocal foldenable
silent! normal! zE
let &fdl = &fdl
let s:l = 29 - ((28 * winheight(0) + 17) / 35)
if s:l < 1 | let s:l = 1 | endif
keepjumps exe s:l
normal! zt
keepjumps 29
normal! 02|
tabnext 1
if exists('s:wipebuf') && len(win_findbuf(s:wipebuf)) == 0 && getbufvar(s:wipebuf, '&buftype') isnot# 'terminal'
  silent exe 'bwipe ' . s:wipebuf
endif
unlet! s:wipebuf
set winheight=1 winwidth=20
let &shortmess = s:shortmess_save
let s:sx = expand("<sfile>:p:r")."x.vim"
if filereadable(s:sx)
  exe "source " . fnameescape(s:sx)
endif
let &g:so = s:so_save | let &g:siso = s:siso_save
set hlsearch
doautoall SessionLoadPost
unlet SessionLoad
" vim: set ft=vim :
