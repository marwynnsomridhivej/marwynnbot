# MarwynnBot Privacy Policy
Thank you for using MarwynnBot. This document details all information MarwynnBot
may collect over the course of its time in your guild. 

## Note
- Any use of the word "guild" or "server" refers to a Discord Server
- "IDs" are the 20 digit unique identifiers assigned to things like
your guild, your user account, any text/voice channel, role, etc

## Guild IDs
- When you add MarwynnBot to a guild it hasn't been added before, it will 
automatically create a database entry. This entry is MarwynnBot's way of storing
per-guild configuration data, such as the server prefix, which is customisable
via a command
- When MarwynnBot leaves any guild, the database entry is not removed. This allows
for the server-specific settings to be stored, so if MarwynnBot rejoins the guild,
the previously set settings are used and do not have to be reconfigured
- The Guild ID is also used in order to validate the existance of saved entries
for features including, but not limited tos Disboard Bump Reminders, AutoRoles,
Reminders, ServerLink, Logging, etc

## User IDs
- MarwynnBot uses user IDs in order to facilitate identity checking when using
certain commands in order to allow only a specific user or users to change command
or feature settings
- A database entry is created, and the user ID is stored for features including,
but not limited to AutoRoles, Reminders, Todo Lists, ServerLink, Nintendo, etc
- The user IDs are never stored for longer than they are needed. If a user's entry
is removed or no longer active, the user ID is removed and no longer stored
- User ID data is not accessible to other users, and is only used internally

## Message IDs
- MarwynnBot uses message IDs in order to facilitate validation when using certian
commands in order to ensure a message exists, or that a user is the author
of a certain message
- A database entry is created, and the message ID is stored for features including,
but not limited to ReactionRoles, Starboard, ServerLink, etc
- Message IDs may be stored, even when the corresponding message becomes inaccessible

## Channel IDs
- MarwynnBot uses channel IDs in order to facilitate validation when using certain
commands or features
- A database entry is created, and the channel ID is stored for features including,
but not limited to Disboard, Leveling, Locks, Redirects, Reminders, ServerLink,
Starboard, Welcome, etc
- Channel IDs may be stored, even when the corresponding channel becomes inaccessible

## Role IDs
- MarwynnBot uses role IDs in order to facilitate the automatic assignment of roles
in certain commands or features
- A database entry is created, and the role ID is stored for features including, 
but not limited to AutoRoles, ReactionRoles, Moderation, Management, Owner, etc
- Role IDs may be stored, even when the corresponding role becomes inaccessible

## Text / Message Content
- MarwynnBot uses user inputted text in order to allow for content customisation
- A database entry is created, and the message content is stored for features where
the command invocation explicitly requests input from the user
- Message content is NEVER stored unless explicitly asked for, and is removed
when the user invokes a command to reset or delete an active feature on their
guild
- The user may, at any time, remove any message content stored by MarwynnBot by
invoking an appropriate command to do so. Every command that accepts and stores
user input has a corresponding command to remove the database entry

## Status and Presence
- MarwynnBot uses status and presence data for its logging feature, however,
none of this data is stored, as it is only received through events and never
entered into any form of storage whatsoever
- As of right now, for non-developers, MarwynnBot only provides the first two
levels of logging for guild events, "Basic" and "Server"
    - The "Basic" logging level only logs MarwynnBot command invocations, and 
logs the user who invoked the command and the channel
where it was invoked
    - The "Server" logging level logs everything from the "Basic"
level, with the addition of guild events, like channel creation/deletion, role 
creation/deletion, user bans/unbans, updating channel positions/info, etc
- In the future, MarwynnBot will allow for non-developers to access the third level, 
"Member"
    - This level logs everything from the aforementioned levels, with the
addition of status and presence data. This includes, but is not limited to changing
statuses (online, away, DND, offline), changes in user rich presence data (like
what game the user is currently playing), username and discriminator changes,
etc
- As previously mentioned, none of this data in the Status and Presence section
is kept in a database or any other form of storage. It is received and processed
only

## Voice Data
- MarwynnBot does not collect or process any voice data transmitted through Discord's
voice channels. MarwynnBot will NEVER listen in on any conversation, and is only
capable of transmitting voice data when requested


# Data Sharing with 3rd Parties
MarwynnBot respects your privacy, therefore, no data is shared between MarwynnBot
and any third parties besides the Discord company.


# Policy Regarding Sensitive Data
Since MarwynnBot stores message content (only when explicitly requested), there 
is a chance that sensitive information is inputted that you do not wish for it
to be stored. In the event something like this occurs, MarwynnBot's developers
will take swift action if you wish that the sensitive information is to be removed
from MarwynnBot's database or any other storage medium. See the [contact](#contact)
section below for ways to get in touch with the developers.

> *note: in this context, sensitive information encompasses information that could
> be personally identifying, including, but not limited to, an email address,
> phone number, government issued ID, etc. In the event that you wish for database
> records containing any non-sensitive information, such as information obtainable
> through Discord's interface (like user IDs, guild IDs, channel IDs, role IDs)
> the MarwynnBot developers will evaluate on a case by case basis, as some data
> is required in order for MarwynnBot to function correctly on your guild*


# Contact
> MarwynnBot Support Server: https://discord.gg/78XXt3Q
> 
> MarwynnBot's Developer: MS Arranges#3060

*I will be happy to remove any information from MarwynnBot's database that you would
like to have removed, or clarify the information on this document if necessary.*