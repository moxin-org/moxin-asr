export const sizeCalculator = (size: number) => {
    if (size < 1024) {
        return size + ' B'
    } else if (size < 1024 * 1024) {
        return (size / 1024).toFixed(2) + ' KB'
    } else if (size < 1024 * 1024 * 1024) {
        return (size / 1024 / 1024).toFixed(2) + ' MB'
    } else {
        return (size / 1024 / 1024 / 1024).toFixed(2) + ' GB'
    }
}

export const getRandomNumInt = (min: number, max: number) => {
    var Range = max - min;
    var Rand = Math.random(); //获取[0-1）的随机数
    return (min + Math.round(Rand * Range)); //放大取整
}

export const formatMs = (ms:any ,all: any) => {
    let ss=ms%1000;ms=(ms-ss)/1000;
    let s=ms%60;ms=(ms-s)/60;
    let m=ms%60;ms=(ms-m)/60;
    let h=ms;
    let t=(h?h+":":"")
        +(all||h+m?("0"+m).substr(-2)+":":"")
        +(all||h+m+s?("0"+s).substr(-2)+"″":"")
        +("00"+ss).substr(-3);
    return t;
}

export const getRandomItems = (arr: [], num: number) => {
    if (arr.length < num) {
        throw new Error('The array does not contain enough elements.');
    }

    // 复制原数组，避免修改原数组
    let tempArray = [...arr];

    // 打乱数组
    for (let i = tempArray.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [tempArray[i], tempArray[j]] = [tempArray[j], tempArray[i]]; // ES6 的解构赋值来交换元素
    }

    // 返回前num个项目
    return tempArray.slice(0, num);
}