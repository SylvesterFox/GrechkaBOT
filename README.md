[![](https://img.shields.io/badge/Version-Release_2.1-brightgreen.svg?style=for-the-badge)](#bot-version)
[![](https://img.shields.io/badge/Python-3.10-blue.svg?style=for-the-badge)](#python)
[![discord.py](https://img.shields.io/badge/discord-py-blue.svg?style=for-the-badge)](https://github.com/Rapptz/discord.py)
[![Discord server](https://discordapp.com/api/guilds/766242638202142741/embed.png)](https://discord.gg/er4WQqc)
=======

# LunaBOT - "IB-WorkShop" Discord server bot.

Привет! Я пони-бот Луна, Я стану Вашим помощником-админом на Вашем сервере Discord, помогу в организации выдачи ролей по реакциям, воспроизведению музыки в голосовых каналах а так же возможности пользователям создавать свои приватные голосовые каналы.<br>
P.S. Так же я могу постить NSFW арты с DerpyBooru, E621 и r34 ;)

---

## Мои слэш-команды.
*Все параметры в <> обязательны*<br>
*Все параметры в [] не обязательны*<br>
- **Я могу выдавать пользователям роли с помощью реакций на сообщениях.**<br>
![image](https://user-images.githubusercontent.com/36928846/215272375-5e19f804-314b-4a02-ae54-88431be4dedf.png)<br>
`/reactroleadd <#channel> <id message> <:emoji:> <@role>` - Создание реакции под сообщением для получения роли.<br>
`/reactroleremove <@role>` - Удаление реакции под сообщением для получения роли.<br>

- **Воспроизведение музыки с YouTube.**<br>
![image](https://user-images.githubusercontent.com/36928846/215279482-c11d8577-3405-42dc-b544-2750bd0194df.png)<br>
`/join [channel]` - Подключение бота к голосовому каналу.<br>
`/play <query>` - Воспроизведение видео с YouTube по поисковому запросу или ссылке.<br> 
`/pause` - Пауза.<br> 
`/resume` - Продолжить воспроизведение.<br> 
`/stop` - Остановка воспроизведения.<br> 
`/leave` - Отключение бота от канала.<br> 
`/nowplaying` - Вывести в чат какой трек сейчас играет.<br> 
`/seek <seek>` - Перемотать на определённый участок.<br> 
`/playlistadd <playlist>` - Добавить плейлист в очередь воспроизведение.<br> 
`/skip` - Пропустить текущий трек.<br> 
`/queue` - Показывает все треки в очереде.<br>

- **Даже не спрашивайте.**<br>
`/pidortest [member]` - реализация легендарной команды с сервера **`Pirate Squad`**, теперь в команде можно указать любого пользователя, а так же улучшен рандом :)<br>
*P.S. Немного изменив, эту команду можно использовать в качестве рандомизатора, рулетки и всего что связано со случайным выбором одного из вариантов. #СлаваOpenSource!*<br>

### Использование команд:<br>
**Команды ролей:**<br>
- `<#channel>` - Текстовый канал *(Например, **`#роли`**)*;<br>
- `<id message>` - ID сообщения *(С включённым режимом разработчика в ДС, щелкаем ПКМ по сообщению, нажимаем **`Копировать ID`**)*;<br>
- `<:emoji:>` - Эмодзи;<br>
- `<@role>` - Роль *(Например: **`@Программист`**)*.<br>
**Команды воспроизведения:**<br>
- `[channel]` - Голосовой канал, а точнее его ID, как получать ID смотри выше в пояснении к `<#channel>` *(Например: **`123456789012345678`**)*<br>
- `<query>` - Запрос/URL *(Например: **`/play Stigmata - Сентябрь`** или **`/play https://youtu.be/9Xz4NV0zsbY`**)*.<br>
- `<seek>` - Перемотка *(Например: **`/seek 1m 1s`**, перемотает трек на 01:01)*.<br>
- `<playlist>` - URL плейлиста *(Например: **`/playlistadd https://www.youtube.com/watch?v=zxECJgdK7t0&list=RDII6DIl98DV8&index=14`**)*.<br>
**Команда с приколом:**<br>
- `[member]` - Пользователь *(Например: **`@IlyaBOT`**)*.<br>
