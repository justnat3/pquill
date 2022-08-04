# Simple and Sane Subnetting Guide (SAG)

## What is subnetting?

Primarily subnetting is meant to break a very large network into many sub networking (subnetting). I also think that subnetting is useful for saving part of your address space by being able to use more of it.

The Private Address Space is defined in RFC1918 

## So how do I do it?
#### 1. Understanding IP(v4)

Out in the wild you will see two things, the address and a mask for that address

The address isn't entirely special in this case, as long as it conforms to RFC1918. The mask however means quite a lot to how an address is understood by a network, its really the bread and butter of our subnetting.

Understanding the parts of our mask we have to understand what parts of the mask actually means in subnetting. This is simple, within a byte you may have (ordered) a 1 or a 0. The leading 1's are the NETWORK portion of the mask. The 0's are the HOST portion of the mask.

Lets say you need 10 sub networks with (172.16.5.0/16)
how do we break that one network owned by one router (x.x.5.x) into 10

1. First take e

```
bits to get to 10
+----------------------+
| 0   0  0  0  1 0 1 0 |
| 128 64 32 16 8 4 2 1 |
+----------------------+
```

2. Take the mask and add the number of bits needed to get to 5 

```
11111111.11111111.11111111.11100000 = 255.255.255.224
```

```
sticking the total number of bits it took to get to 5 to the start of the mask
-----------------------+
| 1   1  1  1  0 0 0 0 |
| 128 64 32 16 8 4 2 1 |
-----------------------+
```

this last diagram will end up being your subnet mask

2. you can use the decimal representation of the last significat bit in the mask as an increment for network ranges 

your ranges would be the following

here is the scope of each of the 5 networks
the addresses here represent the START of the subnet

192.168.5.32
192.168.5.64
192.168.5.96
192.168.5.128
192.168.5.160
etc -> ~255

here are the real ranges

192.168.5.0   - 192.168.5.31
192.168.5.32  - 192.168.5.63
192.168.5.64  - 192.168.5.127
192.168.5.128 - 192.168.5.159

3. the start and end of the ranges are unusable

this is because these are networks, they need a network address, and a broadcast
so here are the usable

192.168.5.1   - 192.168.5.30
192.168.5.31  - 192.168.5.62
192.168.5.65  - 192.168.5.126
192.168.5.129 - 192.168.5.158

and of course as mentioned above the mask for all of these are 255.255.255.224
or /27
