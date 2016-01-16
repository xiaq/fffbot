package main

import (
	"bytes"
	"fmt"
	"io/ioutil"
	"log"
	"strings"

	"github.com/xiaq/tg"
)

type commandMeta struct {
	name        string
	method      func(*Stake, []string, *tg.User) string
	args        string
	description string
}

var commands = []commandMeta{
	{"install", (*Stake).install, "p q ...", "把人捆♂绑到火刑柱上"},
	{"add", (*Stake).add, "i j ...", "添加调料"},
	{"ignite", (*Stake).ignite, "", "开始烧烧烧！"},
	{"water", (*Stake).water, "", "灭火"},
	{"status", (*Stake).status, "", "查询火刑柱状态"},
	{"help", nil, "", "命令帮助"},
}

var commandMap map[string]*commandMeta

func (cm *commandMeta) help() string {
	argsPart := ""
	if cm.args != "" {
		argsPart = " " + cm.args
	}
	return fmt.Sprintf("/fff %s%s: %s", cm.name, argsPart, cm.description)
}

var help string

func init() {
	// Populate helpText
	var buf bytes.Buffer
	buf.WriteString("释放 FFF 团的怒火吧！")
	for _, cm := range commands {
		buf.WriteString("\n" + cm.help())
	}
	help = buf.String()
	// Populate commandMap
	commandMap = make(map[string]*commandMeta)
	for i, cm := range commands {
		commandMap[cm.name] = &commands[i]
	}
}

type state int

const (
	idle state = iota
	installed
	ignited
)

func makeString(things []string) string {
	n := len(things)
	switch n {
	case 0:
		return "啥都没有"
	case 1:
		return things[0]
	default:
		return strings.Join(things[0:n-1], "、") + " 和 " + things[n-1]
	}
}

type Stake struct {
	state     state
	people    []string
	peopleStr string
}

func (s *Stake) stateDesc() string {
	switch s.state {
	case idle:
		return "火刑柱上现在什么都没有。"
	case installed:
		return fmt.Sprintf("火刑柱上现在绑着 %s。", s.peopleStr)
	case ignited:
		return fmt.Sprintf("%s 正在熊熊燃烧。", s.peopleStr)
	default:
		return fmt.Sprintf("火刑柱现在处在作者也不清楚的 %s 状态。", s.state)
	}
}

func (s *Stake) install(people []string, from *tg.User) string {
	if s.state != idle {
		return s.stateDesc()
	}
	if len(people) == 0 {
		return "至少要绑一个人。"
	}
	for i, p := range people {
		people[i] = strings.TrimLeft(p, "@")
	}
	s.people = people
	s.peopleStr = makeString(people)
	s.state = installed
	return fmt.Sprintf("%s 把 %s 绑到了火刑柱上。", from.DisplayName(), s.peopleStr)
}

func (s *Stake) add(things []string, from *tg.User) string {
	if s.state != installed && s.state != ignited {
		return s.stateDesc()
	}
	if len(things) == 0 {
		return "请至少指定一种调料 - -b"
	}
	return fmt.Sprintf("%s 往火刑柱上加了 %s。",
		from.DisplayName(), makeString(things))

}

func (s *Stake) ignite(args []string, from *tg.User) string {
	if s.state != installed {
		return s.stateDesc()
	}
	s.state = ignited
	return fmt.Sprintf("%s 烧起来了！此处应有欢呼。", s.peopleStr)
}

func (s *Stake) water(args []string, from *tg.User) string {
	if s.state != ignited {
		return s.stateDesc()
	}
	s.state = idle
	return fmt.Sprintf("%s 英勇地解救了 %s。", from.DisplayName(), s.peopleStr)
}

func (s *Stake) status(args []string, from *tg.User) string {
	return s.stateDesc()
}

type FFFBot struct {
	*tg.CommandBot
	stakes map[int]*Stake
}

func (b *FFFBot) handleFFF(_ *tg.CommandBot, text string, msg *tg.Message) {
	cmd, args := tg.Split(text, ' ')
	log.Println("fff", cmd, args)
	chatID := msg.Chat.ID
	if b.stakes[chatID] == nil {
		b.stakes[chatID] = &Stake{}
	}
	var reply string
	if cmd == "" {
		cmd = "status"
	}
	cm, ok := commandMap[cmd]
	if cmd == "help" || !ok {
		reply = help
	} else {
		argList := strings.Split(args, " ")
		log.Println(cmd, cm.method, msg.From)
		reply = cm.method(b.stakes[chatID], argList, msg.From)
	}
	b.Get("/sendMessage", tg.Query{
		"chat_id": msg.Chat.ID,
		"text":    reply,
	}, nil)
}

func NewFFFBot(name, token string) *FFFBot {
	b := &FFFBot{tg.NewCommandBot(name, token), make(map[int]*Stake)}
	b.OnCommand("fff", b.handleFFF)
	return b
}

func main() {
	buf, err := ioutil.ReadFile("token.txt")
	if err != nil {
		log.Fatalf("cannot read token file: %s", err)
	}
	token := strings.TrimSpace(string(buf))

	NewFFFBot("xiaqsbot", token).Main()
}
