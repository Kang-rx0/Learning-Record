<template>
<div class = "item">
    <h1> 使用reactive和ref实现响应式数据</h1>
    <h2> 汽车信息：一台 {{ car.brand }} 汽车，价值 {{ car.price }} 万</h2>
    <h2>游戏列表：</h2>
    <ul>
        <li v-for="game in games" :key="game.id">{{ game.name }} : {{ game.price }} 元</li>
    </ul>   
    <h2> 测试： {{  obj.a.b.c.d }}</h2>
    <button @click="changeCarPrice">修改汽车价格</button>
    <button @click="changeFirstGame">修改第一游戏</button>
    <button @click="test">测试</button>
    
</div>
</template>

<script setup lang="ts" name="item">
import { ref } from 'vue'
import { reactive } from 'vue'

let car = ref({ brand: '特斯拉', price: 50 });
let games = reactive([
    { id: 1, name: '塞尔达传说', price: 300 },
    { id: 2, name: '马里奥赛车8', price: 250 },
    { id: 3, name: '动物之森', price: 200 }
]);

// 深层嵌套对象
let obj = ref({
  a:{
    b:{
      c:{
        d:666
      }
    }
  }
});

function changeCarPrice() {
    car.value.price+=100
};
function changeFirstGame() {
    // 这里原本是用 games[0].name = '流星蝴蝶剑' （这里不用.value，因为games是reactive的）
    // 但是会报错说 变量可能未定义，所以用下面这种方法，先做个判断再修改
    const first = games[0];
    if (first) {
        first.name = '流星蝴蝶剑'
    }
};
function test(){
    obj.value.a.b.c.d = 999
}
</script>
