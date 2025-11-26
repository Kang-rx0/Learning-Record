<script lang = "ts">
export default{
    name: 'mine',
    setup() {
        let text = '自定义组件' ;
        let stu ={
                name:"名字",
                age:18,
                gender:"male",
                hobby:{ sport:"basketball",
                        music:"pop",
                        game:"chess"}
            }
        return { text, stu }
    }
}

</script>


<template>
    <div class = mine>
        <h1>标题：{{ text }}</h1>
        <p>{{ stu.name }}</p>
        <p>{{ stu.age }}</p>
        <p>{{ stu.gender }}</p>
        <p>{{ stu.hobby.sport }}</p>
        <p>{{ stu.hobby.music }}</p>
        <p>{{ stu.hobby.game }}</p>
    </div>
</template>


<style>
.read-the-docs {
  color: #888;
}
</style>
