-- demo.luau — exercises most of the luaU -> Zephyr lowering
local function fib(n)
	if n < 2 then return n end
	return fib(n - 1) + fib(n - 2)
end
print("fib(10) =", fib(10))

local players = { "ada", "grace", "linus" }
table.insert(players, "margaret")
table.sort(players)

local scores = { ada = 10, grace = 4, linus = 7 }
scores.margaret = 12

local total = 0
for i, name in ipairs(players) do
	total = total + (scores[name] or 0)
end

local best = players[1]
for _, name in ipairs(players) do
	if (scores[name] or 0) > (scores[best] or 0) then
		best = name
	end
end

print(string.format("%s scored %d (total %d)", best, scores[best], total))
print(("hello " .. best):upper() .. "!")

local sum = 0
for i = 1, 10 do
	sum = sum + i
	if i % 2 == 0 then continue end
end
print("sum 1..10 =", sum)

local x = 10
repeat
	x = x - 3
until x <= 0
print("x after repeat =", x)

local function makeAdder(k)
	local function add(v)
		return v + k
	end
	return add
end
local add5 = makeAdder(5)
print("add5(3) =", add5(3))

local function multi(a, b)
	return a + b, a * b
end
local s, p = multi(3, 4)
print("multi(3,4) =", s, p)

local function variadic(...)
	local t = {...}
	local out = ""
	for i, v in ipairs(t) do
		out = out .. tostring(v)
	end
	return #t, out
end
print("variadic:", variadic("a", "b", "c"))

print("math:", math.floor(3.7), math.sqrt(16), math.pi)
print("os.time() > 0:", os.time() > 0)
print("type checks:", type(1), type("s"), type(true), type({}), type(fib))

-- Roblox-style event shim
local connections = {}
local part = {}
part.Touched = {}
function part.Touched:Connect(fn)
	table.insert(connections, fn)
end
part.Touched:Connect(function(hit)
	print("touched by " .. hit)
end)
connections[1]("roblox player")

-- pairs over a hash table
local flags = { alpha = true, beta = false }
for k, v in pairs(flags) do
	print("flag", k, v)
end

print("done")
