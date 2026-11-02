# PHASE8 — 01_SOURCE_INVENTORY

## Метод и ограничения

Проверка выполнена офлайн по локальному корпусу `C:\ipsw-tools`. Хэши рассчитаны локально; активные службы, устройство и внешние источники не использовались.

## Основные исходники

| Материал | Полный путь | Версия | SHA-256 / UUID | Пригодность |
|---|---|---|---|---|
| amfid B2 | `C:\ipsw-tools\amfid_B2.bin` | iOS 27.2 Beta 2 / `24B5089g` | `39d4d583262c82cdbf4dee2ed694ffc20e99d4589e51a34b127924daa001ccd9`; UUID `3E6D3282-527E-3BC1-8A9F-1C2BABF3A894` | Полный локальный Mach-O slice; пригоден для identity, ObjC metadata и disassembly |
| amfid B3 | `C:\ipsw-tools\amfid_B3.bin` | iOS 27.2 Beta 3 / `24B5099f` | `d331a10135df45100a431aa77e1d65b3d5b012f494f747346dcab4a551b0db8f`; UUID `CFB0C004-41E6-3E06-9D94-0F71E7B3DA2B` | Полный локальный Mach-O slice; пригоден для identity, ObjC metadata и disassembly |
| amfid B2 entitlements | `C:\ipsw-tools\IOS_SECURITY_RESEARCH\ents\amfid_B2.entitlements.plist` | B2 | `e080c72eaf386c6467a1da58b7c6ae36f3d8ee059342d930dfb42cb1a3937a0d` | Пригоден для daemon entitlement inventory; не показывает client launchd policy |
| amfid B3 entitlements | `C:\ipsw-tools\IOS_SECURITY_RESEARCH\ents\amfid_B3.entitlements.plist` | B3 | `e080c72eaf386c6467a1da58b7c6ae36f3d8ee059342d930dfb42cb1a3937a0d` | Пригоден для daemon entitlement inventory; не показывает client launchd policy |
| amfid B2 disassembly | `C:\ipsw-tools\IOS_SECURITY_RESEARCH\amfid_B2_disasm.txt` | B2 | `dbf55bcf7a53b0bef60b0abf277c829285b9367f8f679b45c0eee966aadeb3aa` | Пригоден для static callsite comparison |
| amfid B3 disassembly | `C:\ipsw-tools\IOS_SECURITY_RESEARCH\amfid_B3_disasm.txt` | B3 | `dbf55bcf7a53b0bef60b0abf277c829285b9367f8f679b45c0eee966aadeb3aa` | Пригоден для static callsite comparison |
| extracted amfid info plist B2/B3 | `C:\ipsw-tools\IOS_SECURITY_RESEARCH\info_plists\amfid_B2.info.plist`, `amfid_B3.info.plist` | B2/B3 | оба файла пустые, SHA-256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | Не пригодны для identity или launchd analysis; сохранены как negative evidence |
| sandbox kext B2 | `C:\ipsw-tools\beta2\sandbox\com.apple.security.sandbox` | B2 | `c884a1afe97b8d5f8c21c86eb4e57466edeec9a04b261e45bc9385e5652b7438`; UUID `757D791B-2F6E-38AF-88F4-56996F99B8BC` | Mach-O arm64e kext; policy engine/strings available, no decoded profile/rule map |
| sandbox kext B3 | `C:\ipsw-tools\beta3\sandbox\com.apple.security.sandbox` | B3 | `e41c7ea73ea53164f9f4ec839431dfb8538b0fe831aeb29210ff7f79b46c0329`; UUID `1490B613-0415-3F49-8612-7B8D08328873` | Mach-O arm64e kext; policy engine/strings available, no decoded profile/rule map |
| kernelcache B2 | `C:\ipsw-tools\beta2\24B5089g__iPhone16,1\kernelcache.release.iPhone16,1` | B2 | `35e3266f96981d2fed31f917914fe212c36219431ca190c416cfbeb84f1bfb85` | Present, partial inventory; not decoded for this phase |
| kernelcache B3 | `C:\ipsw-tools\beta3\24B5099f__iPhone16,1\kernelcache.release.iPhone16,1` | B3 | `c31c08194763cb3a6adf51dc945676ac555ed028ac625adda57e8dc45d665a09` | Present, partial inventory; not decoded for this phase |
| dyld shared cache B2 | `C:\ipsw-tools\beta2-dyld\System\Library\Caches\com.apple.dyld\dyld_shared_cache_arm64e` | B2 | `11a4b07ef56f3674a21937980cc1a377e8085e93e72334dc428b02ca26b2ebb8` | Present with split companions; no amfid launchd plist extracted |
| RC diagnostic set | `C:\ipsw-tools\rc-test-24B119\` | iOS 27.2 RC / `24B119` | individual hashes in local corpus | Logs/reports only; no RC amfid, launchd plist or sandbox policy |

## Availability findings

### Available

- B2/B3 amfid binaries and disassemblies;
- B2/B3 amfid daemon entitlements;
- B2/B3 sandbox kexts;
- B2/B3 kernelcache files;
- B2 dyld shared cache split set;
- RC diagnostic reports/logs.

### Missing

- `com.apple.amfid.plist` or `com.apple.MobileFileIntegrity.plist`;
- decoded launchd `MachServices`, `LimitLoadToSessionType`, bootstrap-domain metadata for amfid;
- decoded App Store/system sandbox profiles with effective `mach-lookup` rules;
- RC amfid Mach-O/disassembly/entitlements;
- a complete B3 dyld shared-cache set in the current local corpus;
- Apple SDK/Xcode headers relevant to this service. Windows SDK headers found locally are unrelated.

## Inventory conclusion

The corpus is sufficient to prove that B2/B3 amfid instantiate an NSXPC listener named `com.apple.amfi.nsxpc`, export `AMFIProtocol`, and omit visible getter gates. It is **not sufficient** to prove which client categories can perform Mach lookup, establish a connection, or invoke the endpoint. The sandbox kexts contain policy machinery and related strings, but not a decoded effective policy for this service.
